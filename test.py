import tkinter as tk
from tkinter import messagebox, simpledialog
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime, time as dtime, timedelta
import pytz
import json
import os

# ==========================================
# 1. 基礎參數設定
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "alan9288.yang@gmail.com"
# 建議用環境變數存放 Gmail 應用程式密碼：GMAIL_APP_PASSWORD
# macOS / zsh:
#   export GMAIL_APP_PASSWORD="你的16碼應用程式密碼"
SENDER_PASSWORD = "sory hrqt arao zntp"  # <-- 不要把密碼寫死在程式碼裡
RECEIVER_EMAIL = "alan9288.yang@gmail.com"

CHECK_INTERVAL = 600  # 監控頻率 (10分鐘)
CONFIG_FILE = "config.json"

TZ_TW = pytz.timezone("Asia/Taipei")
TZ_US = pytz.timezone("America/New_York")


# ==========================================
# 2. GUI 管理介面
# ==========================================
class StockManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("智慧股市管家 Pro - 策略中心")
        self.root.geometry("900x700")

        # 狀態
        self.started = False  # 是否按過「儲存設定並開始監控」

        # 資料結構
        self.config = self.load_config()
        self.check_vars = {}  # 存放勾選狀態

        # 視窗關閉事件（按 X）
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- 標題區 ---
        header = tk.Frame(root, pady=10)
        header.pack(side="top", fill="x")
        tk.Label(header, text="📊 全球股市監控策略中心", font=("Microsoft JhengHei", 18, "bold")).pack()
        tk.Label(header, text="勾選您今天想要監控的投資組合，設定完畢後點擊下方按鈕開始。", fg="gray").pack()

        # --- 主內容區 (左右分割) ---
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(expand=True, fill="both")

        # 左邊: 台股
        self.tw_frame = tk.LabelFrame(main_frame, text="🇹🇼 台股市場", font=("Arial", 12, "bold"), padx=5, pady=5)
        self.tw_frame.pack(side="left", expand=True, fill="both", padx=5)
        self.render_market_panel(self.tw_frame, "TW")

        # 右邊: 美股
        self.us_frame = tk.LabelFrame(main_frame, text="🇺🇸 美股市場", font=("Arial", 12, "bold"), padx=5, pady=5)
        self.us_frame.pack(side="right", expand=True, fill="both", padx=5)
        self.render_market_panel(self.us_frame, "US")

        # --- 底部按鈕區 ---
        btn_frame = tk.Frame(root, pady=15, bg="#f0f0f0")
        btn_frame.pack(side="bottom", fill="x")

        self.start_btn = tk.Button(
            btn_frame,
            text="🚀 儲存設定並開始監控",
            bg="#28a745",
            fg="white",
            font=("Arial", 14, "bold"),
            command=self.start_monitoring,
            padx=30,
            pady=10,
            borderwidth=0
        )
        self.start_btn.pack()

    def on_close(self):
        """使用者直接關閉視窗(X) -> 視為不啟動監控"""
        global RUNTIME_CONFIG
        self.started = False
        RUNTIME_CONFIG = {}
        try:
            self.root.quit()
        finally:
            self.root.destroy()

    def load_config(self):
        # 預設設定
        default = {
            "TW": {"thresholds": "+3 +5 -5 -10", "groups": {"權值股": ["2330.TW", "2317.TW"], "航運": ["2603.TW"]}},
            "US": {"thresholds": "+5 +10 -5 -10", "groups": {"科技巨頭": ["AAPL", "NVDA", "TSLA"], "ETF": ["QQQ"]}}
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 基本結構檢查
                if "TW" not in data or "US" not in data:
                    return default
                if "groups" not in data["TW"] or "groups" not in data["US"]:
                    return default
                if "thresholds" not in data["TW"] or "thresholds" not in data["US"]:
                    return default
                return data
            except Exception:
                return default
        return default

    def render_market_panel(self, parent, market):
        # 1. 門檻設定
        tk.Label(parent, text="通知門檻 (如 +3 -5):", anchor="w").pack(fill="x")
        entry_th = tk.Entry(parent)
        entry_th.pack(fill="x", pady=(0, 10))
        entry_th.insert(0, self.config[market].get("thresholds", ""))
        entry_th.bind("<KeyRelease>", lambda event, m=market, e=entry_th: self.update_threshold(m, e.get()))

        # 2. 群組列表容器 (Canvas + Scrollbar 實現滾動)
        list_frame_container = tk.Frame(parent, bd=1, relief="sunken")
        list_frame_container.pack(expand=True, fill="both")

        canvas = tk.Canvas(list_frame_container)
        scrollbar = tk.Scrollbar(list_frame_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 3. 渲染群組
        self.refresh_groups(scrollable_frame, market)

        # 4. 新增群組按鈕
        tk.Button(parent, text="➕ 新增投資組合", command=lambda: self.add_group(scrollable_frame, market)).pack(fill="x", pady=5)

        # 儲存元件參照以便重新整理
        setattr(self, f"{market}_scroll_frame", scrollable_frame)

    def refresh_groups(self, frame, market):
        # 清空舊元件
        for widget in frame.winfo_children():
            widget.destroy()

        groups = self.config[market]["groups"]

        for name, codes in groups.items():
            row = tk.Frame(frame, pady=2, bd=1, relief="flat")
            row.pack(fill="x", anchor="n")

            var = tk.BooleanVar(value=True)
            key = f"{market}_{name}"
            self.check_vars[key] = var

            cb = tk.Checkbutton(row, variable=var)
            cb.pack(side="left")

            code_str = ",".join([c.replace(".TW", "") for c in codes])
            if len(code_str) > 15:
                code_str = code_str[:15] + "..."

            lbl_text = f"{name}\n({code_str})"
            tk.Label(row, text=lbl_text, width=20, anchor="w", justify="left", font=("Arial", 9)).pack(side="left", padx=5)

            tk.Button(row, text="✏️", width=3, command=lambda m=market, g=name: self.edit_group(m, g)).pack(side="right", padx=1)
            tk.Button(row, text="🗑️", width=3, fg="red", command=lambda m=market, g=name: self.delete_group(m, g)).pack(side="right", padx=1)

    # --- 邏輯操作區 ---
    def update_threshold(self, market, value):
        self.config[market]["thresholds"] = value.strip()

    def add_group(self, frame, market):
        name = simpledialog.askstring("新增群組", "請輸入群組名稱 (例如: 存股名單):")
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if name in self.config[market]["groups"]:
            messagebox.showwarning("提示", "群組名稱已存在")
            return

        codes_str = simpledialog.askstring("輸入股票", f"請輸入 {name} 的股票代號 (空白分隔):")
        if not codes_str:
            return

        codes = self.process_codes(market, codes_str)
        if not codes:
            messagebox.showwarning("提示", "未輸入任何有效代號")
            return

        self.config[market]["groups"][name] = codes
        self.refresh_groups(frame, market)

    def edit_group(self, market, group_name):
        current_codes = " ".join(self.config[market]["groups"][group_name])
        new_codes_str = simpledialog.askstring("編輯群組", f"編輯 [{group_name}] 的股票:", initialvalue=current_codes)
        if new_codes_str is None:
            return

        codes = self.process_codes(market, new_codes_str)
        if not codes:
            messagebox.showwarning("提示", "未輸入任何有效代號")
            return

        self.config[market]["groups"][group_name] = codes
        frame = getattr(self, f"{market}_scroll_frame")
        self.refresh_groups(frame, market)

    def delete_group(self, market, group_name):
        if messagebox.askyesno("確認", f"確定要刪除 [{group_name}] 嗎?"):
            del self.config[market]["groups"][group_name]
            frame = getattr(self, f"{market}_scroll_frame")
            self.refresh_groups(frame, market)

    def process_codes(self, market, text):
        raw = text.split()
        final = []
        for c in raw:
            c = c.strip().upper()
            if not c:
                continue
            if market == "TW" and not c.endswith(".TW"):
                c += ".TW"
            final.append(c)
        # 去重但保序
        seen = set()
        out = []
        for x in final:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    def start_monitoring(self):
        # 避免重複點擊
        self.start_btn.config(state="disabled")

        # 1) 存檔：保存所有設定（資料庫）
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("錯誤", f"存檔失敗: {e}")
            self.start_btn.config(state="normal")
            return

        # 2) 產生活動清單（只包含有勾選的群組）
        active_config = {
            "TW": {"enabled": False, "stocks": [], "th_pos": [], "th_neg": []},
            "US": {"enabled": False, "stocks": [], "th_pos": [], "th_neg": []}
        }

        global stock_group_map
        stock_group_map = {}

        for mkt in ["TW", "US"]:
            # 解析門檻
            th_str = self.config[mkt].get("thresholds", "")
            pos, neg = [], []
            for x in th_str.split():
                try:
                    v = float(x)
                    if v > 0:
                        pos.append(v / 100.0)
                    elif v < 0:
                        neg.append(v / 100.0)
                except Exception:
                    pass

            active_config[mkt]["th_pos"] = sorted(pos)
            active_config[mkt]["th_neg"] = sorted(neg, reverse=True)

            # 依勾選加入股票
            has_active_group = False
            for grp_name, codes in self.config[mkt]["groups"].items():
                key = f"{mkt}_{grp_name}"
                if key in self.check_vars and self.check_vars[key].get():
                    has_active_group = True
                    for c in codes:
                        active_config[mkt]["stocks"].append(c)
                        # 若同一股票出現在多群組，保留最後一次（可自行改成 list 收集）
                        stock_group_map[c] = grp_name

            if has_active_group:
                active_config[mkt]["enabled"] = True
                # 去重
                active_config[mkt]["stocks"] = list(set(active_config[mkt]["stocks"]))

        # 3) 傳遞給後端全域變數
        global RUNTIME_CONFIG
        RUNTIME_CONFIG = active_config
        self.started = True

        print("\n✅ 設定完成！GUI 將關閉，監控程式開始運轉...")
        print(f"🇹🇼 台股監控: {len(active_config['TW']['stocks'])} 支")
        print(f"🇺🇸 美股監控: {len(active_config['US']['stocks'])} 支")

        # 4) 正確關閉 GUI：先隱藏，再結束 mainloop，再 destroy（避免 callback 內直接 destroy 的不穩定）
        self.root.withdraw()
        self.root.update_idletasks()
        self.root.after(0, self.root.quit)
        self.root.after(50, self.root.destroy)


# ==========================================
# 3. 監控核心 (後台運行)
# ==========================================
RUNTIME_CONFIG = {}
stock_states = {}       # 紀錄狀態：每檔每天觸發層級
stock_group_map = {}    # symbol -> group name


def get_stock_data_robust(symbol):
    try:
        ticker = yf.Ticker(symbol)

        # 主要：fast_info（較快）
        fi = getattr(ticker, "fast_info", None)
        if fi:
            price = fi.last_price
            prev_close = fi.previous_close
            if price is not None and prev_close is not None and prev_close != 0:
                return float(price), float(prev_close)

        # 備用：history
        hist = ticker.history(period="5d")
        if hist is not None and len(hist) >= 2:
            last = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            if prev != 0:
                return float(last), float(prev)
    except Exception:
        pass
    return None, None


def send_alert_email(market_type, alert_list):
    if not alert_list:
        return False

    try:
        title_prefix = "🇹🇼" if market_type == "TW" else "🇺🇸"
        max_item = max(alert_list, key=lambda x: abs(x["pct"]))
        grp = stock_group_map.get(max_item["symbol"], "自選")

        subject = f"⚠️ {title_prefix} [{grp}] {max_item['symbol']} 波動 {max_item['pct']*100:+.1f}%"

        table_rows = ""
        for item in alert_list:
            pct = item["pct"]

            # 台股：紅漲綠跌；美股：綠漲紅跌
            if market_type == "TW":
                color = "red" if pct > 0 else "green"
            else:
                color = "green" if pct > 0 else "red"

            row = f"""
            <tr>
                <td style="padding:8px; border:1px solid #ddd;">
                    <b>{item['symbol']}</b><br>
                    <span style="font-size:0.8em; color:gray;">{stock_group_map.get(item['symbol'],'')}</span>
                </td>
                <td style="padding:8px; border:1px solid #ddd;">${item['price']:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd;">${item['prev_close']:.2f}</td>
                <td style="padding:8px; border:1px solid #ddd; color:{color}; font-weight:bold;">{pct*100:+.2f}%</td>
                <td style="padding:8px; border:1px solid #ddd; background:#f9f9f9;">觸發 {item['trigger_threshold']*100:+.0f}%</td>
            </tr>"""
            table_rows += row

        body = f"""<html><body>
            <h2>📊 {title_prefix} 監控警報</h2>
            <table style="border-collapse:collapse; width:100%; text-align:center;">
              <tr style="background:#f2f2f2;"><th>股票</th><th>現價</th><th>昨收</th><th>漲跌幅</th><th>門檻</th></tr>
              {table_rows}
            </table>
            <br><p style="color:gray; font-size:0.9em;">Smart Monitor 自動發送</p>
        </body></html>"""

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        if not SENDER_PASSWORD:
            print("⚠️ 未設定 GMAIL_APP_PASSWORD（環境變數），將略過寄信。")
            return False

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"[{datetime.now(TZ_TW).strftime('%H:%M')}] 📧 信件已發送")
        return True
    except Exception as e:
        print(f"❌ 發信失敗: {e}")
        return False


def check_logic(market_type):
    config = RUNTIME_CONFIG.get(market_type)
    if not config or not config.get("enabled"):
        return

    stocks = config["stocks"]
    now_tw = datetime.now(TZ_TW)
    print(f"[{now_tw.strftime('%H:%M')}] 🔍 掃描 {market_type} ({len(stocks)} 支)...")

    pos_th = config["th_pos"]
    neg_th = config["th_neg"]
    alerts = []

    # 用台北日期做「每日重置」
    today_str = now_tw.date().isoformat()

    for symbol in stocks:
        if symbol not in stock_states:
            stock_states[symbol] = {"last_date": None, "level": 0.0}

        # 每日重置觸發層級
        if stock_states[symbol]["last_date"] != today_str:
            stock_states[symbol]["level"] = 0.0
            stock_states[symbol]["last_date"] = today_str

        price, prev = get_stock_data_robust(symbol)
        if price is None or prev is None:
            print(f"   ⚠️ 無數據: {symbol}")
            continue

        pct = (price - prev) / prev

        # 顯示
        emoji = "➖"
        if pct > 0.01:
            emoji = "📈"
        elif pct < -0.01:
            emoji = "📉"
        print(f"   {emoji} {symbol:<10} ${price:>8.2f} ({pct*100:+.2f}%)")

        # 判斷觸發門檻
        trigger = 0.0
        if pct > 0:
            for th in pos_th:
                if pct >= th:
                    trigger = th
                else:
                    break
        elif pct < 0:
            for th in neg_th:
                if pct <= th:
                    trigger = th
                else:
                    break

        # 若達到新的更高層級才發信
        if abs(trigger) > abs(stock_states[symbol]["level"]):
            grp = stock_group_map.get(symbol, "")
            print(f"      >>> 🚨 警報! [{grp}] {trigger*100:+.0f}%")
            alerts.append(
                {
                    "symbol": symbol,
                    "price": price,
                    "prev_close": prev,
                    "pct": pct,
                    "trigger_threshold": trigger,
                }
            )

    if alerts:
        if send_alert_email(market_type, alerts):
            for item in alerts:
                stock_states[item["symbol"]]["level"] = item["trigger_threshold"]

    print("-" * 30)


def smart_sleep_logic():
    now_utc = datetime.now(pytz.utc)
    now_tw = now_utc.astimezone(TZ_TW)
    now_us = now_utc.astimezone(TZ_US)

    is_tw_open = False
    is_us_open = False

    # 台股：週一~週五 09:00~13:30（簡化，未含午休與特殊休市）
    if RUNTIME_CONFIG.get("TW", {}).get("enabled"):
        if now_tw.weekday() < 5 and dtime(9, 0) <= now_tw.time() <= dtime(13, 30):
            is_tw_open = True

    # 美股：週一~週五 09:30~16:00（美東，DST 由 TZ_US 處理）
    if RUNTIME_CONFIG.get("US", {}).get("enabled"):
        if now_us.weekday() < 5 and dtime(9, 30) <= now_us.time() <= dtime(16, 0):
            is_us_open = True

    if is_tw_open:
        return True, "TW", None
    if is_us_open:
        return True, "US", None

    # 休市：計算下次開盤（回傳台北時區）
    candidates = []

    if RUNTIME_CONFIG.get("TW", {}).get("enabled"):
        nt = now_tw.replace(hour=9, minute=0, second=0, microsecond=0)
        if nt < now_tw:
            nt += timedelta(days=1)
        while nt.weekday() >= 5:
            nt += timedelta(days=1)
        candidates.append(nt)  # already TZ_TW

    if RUNTIME_CONFIG.get("US", {}).get("enabled"):
        nu = now_us.replace(hour=9, minute=30, second=0, microsecond=0)
        if nu < now_us:
            nu += timedelta(days=1)
        while nu.weekday() >= 5:
            nu += timedelta(days=1)
        candidates.append(nu.astimezone(TZ_TW))

    next_open = min(candidates) if candidates else None
    return False, None, next_open


# ==========================================
# 4. 主程式
# ==========================================
if __name__ == "__main__":
    # 1) 啟動 GUI
    root = tk.Tk()
    app = StockManagerGUI(root)
    root.mainloop()

    # 2) GUI 關閉後執行監控
    if not RUNTIME_CONFIG or (not RUNTIME_CONFIG.get("TW", {}).get("enabled") and not RUNTIME_CONFIG.get("US", {}).get("enabled")):
        print("未啟動監控，程式結束。")
    else:
        print("\n=== 🟢 背景監控模式已啟動 ===")
        print("設定視窗已關閉，現在開始執行監控循環...")
        print("-" * 30)

        try:
            while True:
                is_active, m_type, n_open = smart_sleep_logic()

                if is_active:
                    check_logic(m_type)
                    time.sleep(CHECK_INTERVAL)
                else:
                    if n_open:
                        now = datetime.now(TZ_TW)
                        wake = n_open - timedelta(minutes=20)
                        secs = (wake - now).total_seconds()
                        if secs > 0:
                            print(f"[{now.strftime('%H:%M')}] 💤 休市。下次開盤: {n_open.strftime('%m/%d %H:%M')}")
                            time.sleep(secs)
                        else:
                            print("⏳ 待機中...")
                            time.sleep(60)
                    else:
                        time.sleep(60)

        except KeyboardInterrupt:
            print("\n程式已手動停止")
