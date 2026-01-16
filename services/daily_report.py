"""
每日報告服務
生成觀測股票摘要和潛力股推薦
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

TZ_TW = pytz.timezone("Asia/Taipei")

# ==========================================
# 熱門股票清單
# ==========================================
TRENDING_STOCKS = {
    "US": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
        "AMD", "NFLX", "DIS", "JPM", "V", "MA", "PYPL", "SQ",
        "COIN", "UBER", "ABNB", "SNOW", "PLTR", "CRM", "ORCL"
    ],
    "TW": [
        "2330.TW", "2317.TW", "2454.TW", "2412.TW", "2308.TW",
        "3711.TW", "2881.TW", "2882.TW", "2303.TW", "3008.TW",
        "2886.TW", "0050.TW", "2891.TW", "2884.TW", "2357.TW",
        "3034.TW", "2382.TW", "6505.TW", "1301.TW", "2002.TW"
    ]
}


def get_stock_analysis(symbol: str) -> Dict:
    """
    取得單一股票的詳細分析
    包含: 價格、漲跌幅、5日變化、成交量變化
    加強錯誤處理：休市、下市、無資料等情況
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # 取得最近 10 天的歷史資料
        hist = ticker.history(period="10d")
        
        # 驗證資料有效性
        if hist is None or hist.empty:
            return {
                "symbol": symbol, 
                "status": "no_data",
                "error": "無交易資料（可能休市、已下市或代號錯誤）",
                "price": None,
                "daily_change": 0,
                "change_5d": 0,
                "volume_change": 0
            }
        
        if len(hist) < 2:
            # 只有一天資料（可能是休市後第一天）
            current_price = hist['Close'].iloc[-1]
            return {
                "symbol": symbol,
                "name": symbol,
                "price": round(current_price, 2) if not pd.isna(current_price) else None,
                "daily_change": 0,
                "change_5d": 0,
                "volume_change": 0,
                "volume": int(hist['Volume'].iloc[-1]) if not pd.isna(hist['Volume'].iloc[-1]) else 0,
                "status": "partial",
                "warning": "資料不足，僅顯示最新價格"
            }
        
        # 檢查價格是否為空值
        if hist['Close'].isna().all():
            return {
                "symbol": symbol,
                "status": "invalid",
                "error": "價格資料無效",
                "price": None,
                "daily_change": 0,
                "change_5d": 0,
                "volume_change": 0
            }
        
        # 取得有效的價格（跳過 NaN）
        valid_closes = hist['Close'].dropna()
        if len(valid_closes) < 2:
            return {
                "symbol": symbol,
                "status": "insufficient",
                "error": "有效價格資料不足",
                "price": round(valid_closes.iloc[-1], 2) if len(valid_closes) > 0 else None,
                "daily_change": 0,
                "change_5d": 0,
                "volume_change": 0
            }
        
        # 基本資訊
        current_price = valid_closes.iloc[-1]
        prev_close = valid_closes.iloc[-2]
        
        # 今日漲跌幅
        if prev_close != 0:
            daily_change = ((current_price - prev_close) / prev_close) * 100
        else:
            daily_change = 0
        
        # 5日變化 (如果有足夠資料)
        if len(valid_closes) >= 5:
            price_5d_ago = valid_closes.iloc[-5]
            change_5d = ((current_price - price_5d_ago) / price_5d_ago) * 100 if price_5d_ago != 0 else 0
        else:
            change_5d = daily_change
        
        # 成交量變化
        valid_volumes = hist['Volume'].dropna()
        if len(valid_volumes) > 0:
            current_volume = valid_volumes.iloc[-1]
            avg_volume = valid_volumes.mean()
            volume_change = ((current_volume - avg_volume) / avg_volume) * 100 if avg_volume > 0 else 0
        else:
            current_volume = 0
            volume_change = 0
        
        # 取得股票名稱
        name = symbol
        try:
            info = ticker.info
            if info:
                name = info.get('shortName', info.get('longName', symbol))
                if not name:
                    name = symbol
        except:
            pass
        
        return {
            "symbol": symbol,
            "name": name,
            "price": round(current_price, 2),
            "daily_change": round(daily_change, 2),
            "change_5d": round(change_5d, 2),
            "volume_change": round(volume_change, 2),
            "volume": int(current_volume),
            "status": "success"
        }
        
    except Exception as e:
        error_msg = str(e)
        # 常見錯誤訊息處理
        if "delisted" in error_msg.lower():
            return {"symbol": symbol, "status": "delisted", "error": "股票已下市", "price": None}
        elif "not found" in error_msg.lower():
            return {"symbol": symbol, "status": "not_found", "error": "找不到股票", "price": None}
        else:
            return {"symbol": symbol, "status": "error", "error": error_msg, "price": None}


def calculate_potential_score(stock_data: Dict) -> float:
    """
    計算潛力分數
    公式: (5日漲幅 × 0.5) + (成交量增幅 × 0.3) + (今日漲幅 × 0.2)
    """
    if stock_data.get("status") != "success":
        return -999
    
    change_5d = stock_data.get("change_5d", 0)
    volume_change = stock_data.get("volume_change", 0)
    daily_change = stock_data.get("daily_change", 0)
    
    # 限制成交量變化的影響（避免異常值）
    volume_score = min(max(volume_change, -50), 100)
    
    score = (change_5d * 0.5) + (volume_score * 0.3) + (daily_change * 0.2)
    return round(score, 2)


def get_watchlist_summary(symbols: List[str]) -> List[Dict]:
    """
    取得觀測清單的股票摘要
    """
    results = []
    for symbol in symbols:
        data = get_stock_analysis(symbol)
        if data.get("status") == "success":
            results.append(data)
    
    # 按今日漲跌幅排序（最佳到最差）
    results.sort(key=lambda x: x.get("daily_change", 0), reverse=True)
    return results


def get_trending_recommendations(market: str = "US", top_n: int = 5, exclude_symbols: List[str] = None) -> List[Dict]:
    """
    取得潛力股推薦
    排除用戶已關注的股票
    """
    if exclude_symbols is None:
        exclude_symbols = []
    
    symbols = TRENDING_STOCKS.get(market, [])
    
    # 排除已關注的股票
    symbols = [s for s in symbols if s not in exclude_symbols]
    
    results = []
    for symbol in symbols:
        data = get_stock_analysis(symbol)
        if data.get("status") == "success":
            data["score"] = calculate_potential_score(data)
            results.append(data)
    
    # 按潛力分數排序
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return results[:top_n]


def generate_daily_report_data(
    watchlist_tw: List[str] = None,
    watchlist_us: List[str] = None
) -> Dict:
    """
    生成每日報告資料
    """
    if watchlist_tw is None:
        watchlist_tw = []
    if watchlist_us is None:
        watchlist_us = []
    
    report_date = datetime.now(TZ_TW).strftime("%Y-%m-%d %H:%M")
    
    # 觀測股票摘要
    watchlist_summary = {
        "TW": get_watchlist_summary(watchlist_tw),
        "US": get_watchlist_summary(watchlist_us)
    }
    
    # 潛力股推薦（排除已關注的）
    trending = {
        "TW": get_trending_recommendations("TW", top_n=5, exclude_symbols=watchlist_tw),
        "US": get_trending_recommendations("US", top_n=5, exclude_symbols=watchlist_us)
    }
    
    # 計算摘要統計
    all_watchlist = watchlist_summary["TW"] + watchlist_summary["US"]
    total_stocks = len(all_watchlist)
    gainers = len([s for s in all_watchlist if s.get("daily_change", 0) > 0])
    losers = total_stocks - gainers
    
    best_performer = max(all_watchlist, key=lambda x: x.get("daily_change", -999)) if all_watchlist else None
    worst_performer = min(all_watchlist, key=lambda x: x.get("daily_change", 999)) if all_watchlist else None
    
    return {
        "report_date": report_date,
        "summary": {
            "total_stocks": total_stocks,
            "gainers": gainers,
            "losers": losers,
            "best_performer": best_performer,
            "worst_performer": worst_performer
        },
        "watchlist": watchlist_summary,
        "trending": trending
    }


def generate_market_report_data(
    market: str,
    watchlist: List[str] = None
) -> Dict:
    """
    生成單一市場的報告資料（台股或美股分開）
    market: "TW" 或 "US"
    """
    if watchlist is None:
        watchlist = []
    
    market = market.upper()
    report_date = datetime.now(TZ_TW).strftime("%Y-%m-%d %H:%M")
    
    market_info = {
        "TW": {"name": "台股", "flag": "🇹🇼", "close_time": "13:30"},
        "US": {"name": "美股", "flag": "🇺🇸", "close_time": "05:00 (台灣時間)"}
    }
    
    info = market_info.get(market, market_info["US"])
    
    # 觀測股票摘要
    watchlist_summary = get_watchlist_summary(watchlist)
    
    # 潛力股推薦（排除已關注的）
    trending = get_trending_recommendations(market, top_n=5, exclude_symbols=watchlist)
    
    # 計算摘要統計
    total_stocks = len(watchlist_summary)
    gainers = len([s for s in watchlist_summary if s.get("daily_change", 0) > 0])
    losers = total_stocks - gainers
    
    best_performer = max(watchlist_summary, key=lambda x: x.get("daily_change", -999)) if watchlist_summary else None
    worst_performer = min(watchlist_summary, key=lambda x: x.get("daily_change", 999)) if watchlist_summary else None
    
    return {
        "report_date": report_date,
        "market": market,
        "market_name": info["name"],
        "market_flag": info["flag"],
        "close_time": info["close_time"],
        "summary": {
            "total_stocks": total_stocks,
            "gainers": gainers,
            "losers": losers,
            "best_performer": best_performer,
            "worst_performer": worst_performer
        },
        "watchlist": watchlist_summary,
        "trending": trending
    }


def generate_market_report_html(report_data: Dict, user_name: str = "User") -> str:
    """
    生成單一市場的 HTML 報告
    """
    report_date = report_data["report_date"]
    market = report_data["market"]
    market_name = report_data["market_name"]
    market_flag = report_data["market_flag"]
    summary = report_data["summary"]
    watchlist = report_data["watchlist"]
    trending = report_data["trending"]
    
    is_tw = market == "TW"
    
    # 格式化觀測股票列表
    def format_stock_row(stock):
        symbol = stock["symbol"].replace(".TW", "") if is_tw else stock["symbol"]
        name = stock.get("name", "")[:12]
        price = stock["price"]
        daily = stock["daily_change"]
        change_5d = stock["change_5d"]
        volume_change = stock["volume_change"]
        
        # 台股紅漲綠跌，美股綠漲紅跌
        if is_tw:
            color = "#ef4444" if daily >= 0 else "#22c55e"
        else:
            color = "#22c55e" if daily >= 0 else "#ef4444"
        
        icon = "🔺" if daily >= 0 else "🔻"
        sign = "+" if daily >= 0 else ""
        sign_5d = "+" if change_5d >= 0 else ""
        
        return f"""
        <tr>
            <td style="padding: 15px; border-bottom: 1px solid #334155;">
                {icon} <strong style="font-size: 16px;">{symbol}</strong>
                <div style="color: #888; font-size: 12px; margin-top: 4px;">{name}</div>
            </td>
            <td style="padding: 15px; border-bottom: 1px solid #334155; text-align: right;">
                <div style="font-size: 18px; font-weight: bold;">${price:,.2f}</div>
            </td>
            <td style="padding: 15px; border-bottom: 1px solid #334155; text-align: right;">
                <div style="color: {color}; font-size: 16px; font-weight: bold;">{sign}{daily}%</div>
                <div style="color: #888; font-size: 12px;">5日: {sign_5d}{change_5d}%</div>
            </td>
            <td style="padding: 15px; border-bottom: 1px solid #334155; text-align: right;">
                <div style="color: #888; font-size: 12px;">
                    成交量 {'+' if volume_change >= 0 else ''}{volume_change:.0f}%
                </div>
            </td>
        </tr>
        """
    
    # 格式化潛力股
    def format_trending_stock(stock, rank):
        symbol = stock["symbol"].replace(".TW", "") if is_tw else stock["symbol"]
        name = stock.get("name", "")[:15]
        price = stock["price"]
        change_5d = stock["change_5d"]
        daily_change = stock["daily_change"]
        volume_change = stock["volume_change"]
        score = stock.get("score", 0)
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        medal = medals[rank] if rank < len(medals) else f"{rank+1}."
        
        return f"""
        <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 24px;">{medal}</span>
                    <strong style="font-size: 18px; margin-left: 10px;">{symbol}</strong>
                    <span style="color: #888; margin-left: 10px;">{name}</span>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 20px; font-weight: bold;">${price:,.2f}</div>
                    <div style="color: #22c55e; font-size: 14px;">5日: +{change_5d}%</div>
                </div>
            </div>
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #334155;">
                <span style="background: #22c55e22; color: #22c55e; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                    今日 {'+' if daily_change >= 0 else ''}{daily_change}%
                </span>
                <span style="background: #38bdf822; color: #38bdf8; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px;">
                    成交量 {'+' if volume_change >= 0 else ''}{volume_change:.0f}%
                </span>
                <span style="background: #f59e0b22; color: #f59e0b; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-left: 8px;">
                    潛力分數: {score}
                </span>
            </div>
        </div>
        """
    
    watchlist_rows = "".join([format_stock_row(s) for s in watchlist])
    trending_html = "".join([format_trending_stock(s, i) for i, s in enumerate(trending)])
    
    # 最佳/最差表現者
    best = summary.get("best_performer")
    worst = summary.get("worst_performer")
    best_text = f"{best['symbol'].replace('.TW', '')} (+{best['daily_change']}%)" if best else "N/A"
    worst_text = f"{worst['symbol'].replace('.TW', '')} ({worst['daily_change']}%)" if worst else "N/A"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; margin: 0;">
        <div style="max-width: 700px; margin: 0 auto;">
            <!-- Header -->
            <div style="text-align: center; padding: 30px 0; border-bottom: 2px solid #334155;">
                <div style="font-size: 48px; margin-bottom: 10px;">{market_flag}</div>
                <h1 style="color: #38bdf8; margin: 0; font-size: 28px;">{market_name}收盤報告</h1>
                <p style="color: #94a3b8; margin-top: 10px; font-size: 14px;">{report_date}</p>
            </div>
            
            <!-- Summary Cards -->
            <div style="display: flex; justify-content: space-around; padding: 25px 0; flex-wrap: wrap;">
                <div style="text-align: center; min-width: 100px;">
                    <div style="font-size: 36px; font-weight: bold; color: #22c55e;">{summary['gainers']}</div>
                    <div style="color: #888; font-size: 14px;">上漲</div>
                </div>
                <div style="text-align: center; min-width: 100px;">
                    <div style="font-size: 36px; font-weight: bold; color: #ef4444;">{summary['losers']}</div>
                    <div style="color: #888; font-size: 14px;">下跌</div>
                </div>
                <div style="text-align: center; min-width: 100px;">
                    <div style="font-size: 36px; font-weight: bold; color: #38bdf8;">{summary['total_stocks']}</div>
                    <div style="color: #888; font-size: 14px;">總計</div>
                </div>
            </div>
            
            <!-- Best/Worst -->
            <div style="background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 30px;">
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                    <div style="margin: 5px 0;">
                        🏆 最佳表現: <strong style="color: #22c55e;">{best_text}</strong>
                    </div>
                    <div style="margin: 5px 0;">
                        📉 最差表現: <strong style="color: #ef4444;">{worst_text}</strong>
                    </div>
                </div>
            </div>
            
            <!-- My Watchlist -->
            <h2 style="color: #38bdf8; border-bottom: 2px solid #38bdf8; padding-bottom: 10px; margin-top: 30px;">
                📈 我的{market_name}觀測
            </h2>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="color: #64748b; font-size: 12px; text-transform: uppercase;">
                        <th style="text-align: left; padding: 12px;">股票</th>
                        <th style="text-align: right; padding: 12px;">收盤價</th>
                        <th style="text-align: right; padding: 12px;">漲跌幅</th>
                        <th style="text-align: right; padding: 12px;">成交量</th>
                    </tr>
                </thead>
                <tbody>
                    {watchlist_rows if watchlist_rows else '<tr><td colspan="4" style="text-align: center; color: #666; padding: 30px;">尚無觀測股票</td></tr>'}
                </tbody>
            </table>
            
            <!-- Trending -->
            <h2 style="color: #f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom: 10px; margin-top: 40px;">
                🌟 {market_name}潛力股推薦
            </h2>
            <p style="color: #888; margin-bottom: 20px; font-size: 14px;">
                根據 5 日漲幅 (50%)、成交量變化 (30%)、今日漲幅 (20%) 綜合評分
            </p>
            
            {trending_html if trending_html else '<p style="color: #666; text-align: center; padding: 30px;">暫無推薦</p>'}
            
            <!-- Footer -->
            <div style="text-align: center; padding: 30px 0; border-top: 1px solid #334155; margin-top: 40px;">
                <p style="color: #64748b; font-size: 12px;">
                    此報告由股票監控系統自動生成<br>
                    投資有風險，請謹慎評估
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_report_html(report_data: Dict, user_name: str = "User") -> str:
    """
    生成 HTML 格式的報告郵件
    """
    report_date = report_data["report_date"]
    summary = report_data["summary"]
    watchlist = report_data["watchlist"]
    trending = report_data["trending"]
    
    # 格式化觀測股票列表
    def format_stock_row(stock, is_tw=False):
        symbol = stock["symbol"].replace(".TW", "") if is_tw else stock["symbol"]
        name = stock.get("name", "")[:10]
        price = stock["price"]
        daily = stock["daily_change"]
        change_5d = stock["change_5d"]
        
        color = "#22c55e" if daily >= 0 else "#ef4444"
        icon = "🟢" if daily >= 0 else "🔴"
        sign = "+" if daily >= 0 else ""
        sign_5d = "+" if change_5d >= 0 else ""
        
        return f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #333;">
                {icon} <strong>{symbol}</strong>
                <span style="color: #888; font-size: 12px;">{name}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; text-align: right;">
                ${price:,.2f}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; text-align: right; color: {color};">
                {sign}{daily}%
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; text-align: right; color: #888;">
                5日: {sign_5d}{change_5d}%
            </td>
        </tr>
        """
    
    # 格式化潛力股
    def format_trending_stock(stock, rank, is_tw=False):
        symbol = stock["symbol"].replace(".TW", "") if is_tw else stock["symbol"]
        name = stock.get("name", "")[:15]
        price = stock["price"]
        change_5d = stock["change_5d"]
        volume_change = stock["volume_change"]
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        medal = medals[rank] if rank < len(medals) else f"{rank+1}."
        
        vol_text = "成交量增加" if volume_change > 0 else "成交量減少"
        
        return f"""
        <div style="background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 20px;">{medal}</span>
                    <strong style="font-size: 16px; margin-left: 8px;">{symbol}</strong>
                    <span style="color: #888; margin-left: 8px;">{name}</span>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 18px;">${price:,.2f}</div>
                    <div style="color: #22c55e;">5日: +{change_5d}%</div>
                </div>
            </div>
            <div style="color: #888; font-size: 12px; margin-top: 8px;">
                {vol_text} {abs(volume_change):.0f}%
            </div>
        </div>
        """
    
    # 組合 HTML
    watchlist_tw_rows = "".join([format_stock_row(s, True) for s in watchlist["TW"]])
    watchlist_us_rows = "".join([format_stock_row(s, False) for s in watchlist["US"]])
    
    trending_tw_html = "".join([format_trending_stock(s, i, True) for i, s in enumerate(trending["TW"])])
    trending_us_html = "".join([format_trending_stock(s, i, False) for i, s in enumerate(trending["US"])])
    
    # 最佳/最差表現者
    best = summary.get("best_performer")
    worst = summary.get("worst_performer")
    best_text = f"{best['symbol']} (+{best['daily_change']}%)" if best else "N/A"
    worst_text = f"{worst['symbol']} ({worst['daily_change']}%)" if worst else "N/A"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; margin: 0;">
        <div style="max-width: 700px; margin: 0 auto;">
            <!-- Header -->
            <div style="text-align: center; padding: 30px 0; border-bottom: 1px solid #334155;">
                <h1 style="color: #38bdf8; margin: 0;">📊 每日股票報告</h1>
                <p style="color: #94a3b8; margin-top: 10px;">{report_date}</p>
            </div>
            
            <!-- Summary Cards -->
            <div style="display: flex; justify-content: space-between; padding: 20px 0; flex-wrap: wrap;">
                <div style="background: linear-gradient(135deg, #22c55e22, #22c55e11); padding: 20px; border-radius: 12px; flex: 1; margin: 5px; text-align: center; min-width: 120px;">
                    <div style="font-size: 28px; font-weight: bold; color: #22c55e;">{summary['gainers']}</div>
                    <div style="color: #888;">上漲</div>
                </div>
                <div style="background: linear-gradient(135deg, #ef444422, #ef444411); padding: 20px; border-radius: 12px; flex: 1; margin: 5px; text-align: center; min-width: 120px;">
                    <div style="font-size: 28px; font-weight: bold; color: #ef4444;">{summary['losers']}</div>
                    <div style="color: #888;">下跌</div>
                </div>
                <div style="background: linear-gradient(135deg, #38bdf822, #38bdf811); padding: 20px; border-radius: 12px; flex: 1; margin: 5px; text-align: center; min-width: 120px;">
                    <div style="font-size: 28px; font-weight: bold; color: #38bdf8;">{summary['total_stocks']}</div>
                    <div style="color: #888;">總計</div>
                </div>
            </div>
            
            <!-- Best/Worst -->
            <div style="background: #1e293b; padding: 15px 20px; border-radius: 12px; margin-bottom: 30px;">
                <div style="display: flex; justify-content: space-between;">
                    <div>🏆 最佳表現: <strong style="color: #22c55e;">{best_text}</strong></div>
                    <div>📉 最差表現: <strong style="color: #ef4444;">{worst_text}</strong></div>
                </div>
            </div>
            
            <!-- My Watchlist -->
            <h2 style="color: #38bdf8; border-bottom: 2px solid #38bdf8; padding-bottom: 10px;">📈 我的觀測股票</h2>
            
            <!-- US Stocks -->
            <h3 style="color: #94a3b8;">🇺🇸 美股</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="color: #64748b; font-size: 12px;">
                        <th style="text-align: left; padding: 8px;">股票</th>
                        <th style="text-align: right; padding: 8px;">價格</th>
                        <th style="text-align: right; padding: 8px;">今日</th>
                        <th style="text-align: right; padding: 8px;">趨勢</th>
                    </tr>
                </thead>
                <tbody>
                    {watchlist_us_rows if watchlist_us_rows else '<tr><td colspan="4" style="text-align: center; color: #666; padding: 20px;">尚無觀測股票</td></tr>'}
                </tbody>
            </table>
            
            <!-- TW Stocks -->
            <h3 style="color: #94a3b8;">🇹🇼 台股</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="color: #64748b; font-size: 12px;">
                        <th style="text-align: left; padding: 8px;">股票</th>
                        <th style="text-align: right; padding: 8px;">價格</th>
                        <th style="text-align: right; padding: 8px;">今日</th>
                        <th style="text-align: right; padding: 8px;">趨勢</th>
                    </tr>
                </thead>
                <tbody>
                    {watchlist_tw_rows if watchlist_tw_rows else '<tr><td colspan="4" style="text-align: center; color: #666; padding: 20px;">尚無觀測股票</td></tr>'}
                </tbody>
            </table>
            
            <!-- Trending -->
            <h2 style="color: #f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom: 10px;">🌟 潛力股推薦</h2>
            <p style="color: #888; margin-bottom: 20px;">根據 5 日漲幅和成交量變化分析</p>
            
            <h3 style="color: #94a3b8;">🇺🇸 美股潛力股</h3>
            {trending_us_html if trending_us_html else '<p style="color: #666;">暫無推薦</p>'}
            
            <h3 style="color: #94a3b8; margin-top: 20px;">🇹🇼 台股潛力股</h3>
            {trending_tw_html if trending_tw_html else '<p style="color: #666;">暫無推薦</p>'}
            
            <!-- Footer -->
            <div style="text-align: center; padding: 30px 0; border-top: 1px solid #334155; margin-top: 30px;">
                <p style="color: #64748b; font-size: 12px;">
                    此報告由股票監控系統自動生成<br>
                    投資有風險，請謹慎評估
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
