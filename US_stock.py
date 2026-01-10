import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime, time as dtime, timedelta
import pytz

# ==========================================
# 1. 設定區域
# ==========================================
STOCKS = ["AAPL", "AMZN", "NVDA", "TSLA", "TSM"]
TIERS = [0.05, 0.10, 0.15] 

# 盤中掃描頻率 (10 分鐘)
CHECK_INTERVAL = 600 

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "F114152149@nkust.edu.tw"
# ⚠️ 請填入你的應用程式密碼
SENDER_PASSWORD = "eegd bbhp lwsh fvgg" 
RECEIVER_EMAIL = "alan9288.yang@gmail.com"

stock_states = {symbol: {'last_date': None, 'level': 0} for symbol in STOCKS}

# ==========================================
# 2. 核心功能函式
# ==========================================

def get_market_status():
    """判斷美股狀態 (美東 09:30 - 16:00)"""
    tz_ny = pytz.timezone('America/New_York')
    now_ny = datetime.now(tz_ny)
    
    if now_ny.weekday() >= 5: return False, "週末休市"
    holidays = [(1, 1), (6, 19), (7, 4), (11, 28), (12, 25)]
    if (now_ny.month, now_ny.day) in holidays: return False, "國定假日休市"

    current_time = now_ny.time()
    market_start = dtime(9, 30)
    market_end = dtime(16, 0)

    if market_start <= current_time <= market_end:
        return True, "開盤中"
    else:
        return False, f"休市 ({current_time.strftime('%H:%M')})"

def smart_sleep_until_open():
    """
    智慧休眠邏輯：
    直接計算距離「下次開盤 (NY 09:30)」還有多久，
    然後睡到「開盤前 30 分鐘」再醒來。
    """
    tz_ny = pytz.timezone('America/New_York')
    now_ny = datetime.now(tz_ny)
    
    # 設定目標：今天的 09:30
    target_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # 如果現在已經過了 09:30 (例如現在是下午或晚上)，目標就是「明天的 09:30」
    if now_ny > target_open:
        target_open = target_open + timedelta(days=1)
    
    # 計算還要等幾秒
    seconds_until_open = (target_open - now_ny).total_seconds()
    
    # 如果距離開盤還很久 (例如超過 1 小時)
    # 我們就睡到「開盤前 30 分鐘」再叫醒程式
    if seconds_until_open > 3600:
        sleep_seconds = seconds_until_open - 1800 # 扣掉 30 分鐘 (1800秒) 的緩衝
        
        # 換算一下這代表台灣時間幾點醒來
        tz_tw = pytz.timezone('Asia/Taipei')
        wake_up_time = datetime.now(tz_tw) + timedelta(seconds=sleep_seconds)
        
        print(f"[{datetime.now().strftime('%H:%M')}] 💤 距離下次開盤還很久，切換至長睡眠模式...")
        print(f"   >>> 預計睡眠 {sleep_seconds/3600:.1f} 小時")
        print(f"   >>> 下次喚醒時間：台灣時間 {wake_up_time.strftime('%m/%d %H:%M')} (開盤前 30 分鐘)")
        
        time.sleep(sleep_seconds)
    else:
        # 如果距離開盤不到 1 小時，就進入「待機模式」，每 60 秒檢查一次
        print(f"\r[{datetime.now().strftime('%H:%M')}] ⏳ 快開盤了，待機中...", end="")
        time.sleep(60)

def send_alert_email(alert_list):
    """發送通知信 (與之前相同)"""
    if not alert_list: return False
    try:
        max_tier = max([item['trigger_pct'] for item in alert_list])
        count = len(alert_list)
        if count > 1:
            subject = f"⚠️ 美股警報: {count} 檔股票跌幅擴大 (觸發 {max_tier*100:.0f}% 門檻)"
        else:
            stock = alert_list[0]
            subject = f"⚠️ 股價警報: {stock['symbol']} 跌幅突破 {stock['trigger_pct']*100:.0f}%"
        
        table_rows = ""
        for item in alert_list:
            color = "#ff9800"
            if item['trigger_pct'] >= 0.15: color = "#8b0000"
            elif item['trigger_pct'] >= 0.10: color = "red"

            row = f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><b>{item['symbol']}</b></td>
                <td style="padding: 8px; border: 1px solid #ddd;">${item['price']:.2f}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${item['base']:.2f}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: {color}; font-weight: bold;">
                    {item['current_drop']*100:.2f}%
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; background-color: #fff3e0;">
                    突破 {item['trigger_pct']*100:.0f}% 關卡
                </td>
            </tr>
            """
            table_rows += row

        body = f"""
        <html>
          <body>
            <h2 style="color: #d9534f;">📉 階梯式下跌警報</h2>
            <p>監測到以下股票跌勢擴大，突破新的下跌關卡：</p>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px; text-align: center;">
              <thead>
                <tr style="background-color: #f2f2f2;">
                  <th style="padding: 8px; border: 1px solid #ddd;">代號</th>
                  <th style="padding: 8px; border: 1px solid #ddd;">現價</th>
                  <th style="padding: 8px; border: 1px solid #ddd;">月基準</th>
                  <th style="padding: 8px; border: 1px solid #ddd;">目前跌幅</th>
                  <th style="padding: 8px; border: 1px solid #ddd;">觸發等級</th>
                </tr>
              </thead>
              <tbody>
                {table_rows}
              </tbody>
            </table>
            <p style="font-size: 0.9em; color: #666;"><br>系統自動發送</p>
          </body>
        </html>
        """
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[{datetime.now()}] 📧 警報信件已發送！")
        return True
    except Exception as e:
        print(f"❌ 發信失敗: {e}")
        return False

def check_prices_logic():
    """執行檢查邏輯"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 執行掃描 (目標: 5% -> 10% -> 15%)...")
    alerts_to_send = []
    today_date = datetime.now().date()

    for symbol in STOCKS:
        try:
            if stock_states[symbol]['last_date'] != today_date:
                stock_states[symbol]['level'] = 0
                stock_states[symbol]['last_date'] = today_date

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            if len(hist) == 0: continue

            baseline_price = hist['Close'].iloc[0]
            try:
                current_price = ticker.info.get('regularMarketPrice')
                if not current_price: current_price = hist['Close'].iloc[-1]
            except:
                current_price = hist['Close'].iloc[-1]

            if not current_price or not baseline_price: continue

            change_pct = (current_price - baseline_price) / baseline_price
            drop_magnitude = abs(change_pct)

            current_tier_level = 0
            trigger_pct = 0.0

            if drop_magnitude >= 0.15:
                current_tier_level = 3
                trigger_pct = 0.15
            elif drop_magnitude >= 0.10:
                current_tier_level = 2
                trigger_pct = 0.10
            elif drop_magnitude >= 0.05:
                current_tier_level = 1
                trigger_pct = 0.05

            last_recorded_level = stock_states[symbol]['level']

            if current_tier_level > last_recorded_level:
                print(f"   >>> 🚨 {symbol} 跌幅 {drop_magnitude*100:.2f}%，觸發 {trigger_pct*100:.0f}% 門檻")
                alerts_to_send.append({
                    'symbol': symbol,
                    'price': current_price,
                    'base': baseline_price,
                    'current_drop': drop_magnitude,
                    'trigger_pct': trigger_pct,
                    'new_level': current_tier_level
                })
            else:
                print(f"   {symbol:<5}: ${current_price:>7.2f} | 跌幅: {change_pct*100:>6.2f}% (目前等級: {last_recorded_level})")

        except Exception as e:
            print(f"   讀取 {symbol} 失敗: {e}")

    if len(alerts_to_send) > 0:
        if send_alert_email(alerts_to_send):
            for item in alerts_to_send:
                sym = item['symbol']
                stock_states[sym]['level'] = item['new_level']
    print("-" * 30)

# ==========================================
# 3. 主程式
# ==========================================
if __name__ == "__main__":
    print("=== 智慧型省電美股監控系統 ===")
    print(f"監控名單: {STOCKS}")
    print(f"機制: 盤中每 10 分鐘檢查，收盤後自動長睡眠至開盤前")
    print("----------------------------------------")

    while True:
        try:
            is_open, msg = get_market_status()

            if is_open:
                # === 開盤中 ===
                # 1. 執行檢查
                check_prices_logic()
                
                # 2. 休息 10 分鐘
                time.sleep(CHECK_INTERVAL) 
            else:
                # === 休市中 ===
                # 呼叫我們新寫的「智慧休眠」功能
                # 它會自己算要睡多久，不用我們操心
                smart_sleep_until_open()

        except KeyboardInterrupt:
            print("\n程式已停止")
            break
        except Exception as e:
            print(f"\n發生錯誤: {e}")
            time.sleep(60)