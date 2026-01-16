"""
股票詳細資訊服務
提供股票的完整資訊、新聞和推薦理由
"""

import yfinance as yf
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
import pytz

TZ_TW = pytz.timezone("Asia/Taipei")

# Finnhub API Key
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")


def generate_recommendation_reasons(stock_data: Dict) -> List[str]:
    """
    根據股票數據自動生成推薦理由
    """
    if stock_data.get("status") != "success":
        return ["⚠️ 資料不完整，無法生成推薦理由"]
    
    reasons = []
    
    change_5d = stock_data.get("change_5d", 0)
    volume_change = stock_data.get("volume_change", 0)
    daily_change = stock_data.get("daily_change", 0)
    score = stock_data.get("score", 0)
    
    # 基於 5 日漲幅
    if change_5d > 10:
        reasons.append(f"🔥 近 5 日強勢上漲 {change_5d}%，動能強勁")
    elif change_5d > 5:
        reasons.append(f"📈 5 日漲幅 {change_5d}%，趨勢向上")
    elif change_5d > 2:
        reasons.append(f"📊 5 日穩健上漲 {change_5d}%")
    elif change_5d > 0:
        reasons.append(f"➡️ 5 日小幅上漲 {change_5d}%")
    
    # 基於成交量
    if volume_change > 100:
        reasons.append(f"💰 成交量較平均增加 {volume_change:.0f}%，資金大幅流入")
    elif volume_change > 50:
        reasons.append(f"📊 成交量放大 {volume_change:.0f}%，市場關注度提升")
    elif volume_change > 20:
        reasons.append(f"📈 成交量增加 {volume_change:.0f}%，買盤活躍")
    
    # 基於今日表現
    if daily_change > 5:
        reasons.append(f"⚡ 今日大漲 {daily_change}%，短線強勢表現")
    elif daily_change > 3:
        reasons.append(f"🚀 今日漲幅 {daily_change}%，表現亮眼")
    elif daily_change > 1:
        reasons.append(f"✅ 今日上漲 {daily_change}%，維持正向走勢")
    
    # 綜合評分
    if score > 10:
        reasons.append("⭐ 綜合潛力分數極高，短期表現優異")
    elif score > 5:
        reasons.append("📌 綜合評分良好，值得關注")
    
    if not reasons:
        reasons.append("📊 綜合數據分析後列入推薦名單")
    
    return reasons


def get_company_info(symbol: str) -> Dict:
    """
    取得公司基本資訊
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if not info:
            return {"symbol": symbol, "error": "無公司資訊"}
        
        return {
            "symbol": symbol,
            "name": info.get("shortName") or info.get("longName") or symbol,
            "sector": info.get("sector", "未知"),
            "industry": info.get("industry", "未知"),
            "market_cap": info.get("marketCap"),
            "market_cap_display": format_market_cap(info.get("marketCap")),
            "pe_ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
            "dividend_yield": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else None,
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "description": info.get("longBusinessSummary", "")[:500] if info.get("longBusinessSummary") else "",
            "website": info.get("website", ""),
            "country": info.get("country", ""),
            "currency": info.get("currency", "USD"),
            "status": "success"
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "status": "error"}


def format_market_cap(market_cap: Optional[int]) -> str:
    """格式化市值顯示"""
    if not market_cap:
        return "N/A"
    if market_cap >= 1e12:
        return f"${market_cap/1e12:.2f}T"
    elif market_cap >= 1e9:
        return f"${market_cap/1e9:.2f}B"
    elif market_cap >= 1e6:
        return f"${market_cap/1e6:.2f}M"
    else:
        return f"${market_cap:,.0f}"


def get_stock_news(symbol: str, limit: int = 5) -> List[Dict]:
    """
    取得股票相關新聞
    使用 Finnhub API
    """
    if not FINNHUB_API_KEY:
        return [{
            "title": "新聞功能需要設定 Finnhub API Key",
            "source": "System",
            "url": "",
            "date": ""
        }]
    
    # 移除台股後綴
    clean_symbol = symbol.replace(".TW", "")
    
    try:
        # 取得最近 7 天的新聞
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        url = f"https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": clean_symbol,
            "from": from_date,
            "to": to_date,
            "token": FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            news_list = response.json()
            
            if not news_list:
                return [{
                    "title": "近期無相關新聞",
                    "source": "",
                    "url": "",
                    "date": ""
                }]
            
            # 整理新聞格式
            formatted_news = []
            for news in news_list[:limit]:
                formatted_news.append({
                    "title": news.get("headline", ""),
                    "summary": news.get("summary", "")[:200] + "..." if news.get("summary") else "",
                    "source": news.get("source", ""),
                    "url": news.get("url", ""),
                    "date": datetime.fromtimestamp(news.get("datetime", 0)).strftime("%Y-%m-%d %H:%M") if news.get("datetime") else "",
                    "image": news.get("image", "")
                })
            
            return formatted_news
        else:
            return [{"title": f"新聞取得失敗: {response.status_code}", "source": "", "url": "", "date": ""}]
            
    except Exception as e:
        return [{"title": f"新聞取得錯誤: {str(e)}", "source": "", "url": "", "date": ""}]


def get_stock_detail(symbol: str, stock_data: Dict = None) -> Dict:
    """
    取得股票完整詳細資訊
    包含：基本資料、推薦理由、新聞
    """
    from services.daily_report import get_stock_analysis, calculate_potential_score
    
    # 如果沒有提供 stock_data，則重新獲取
    if not stock_data:
        stock_data = get_stock_analysis(symbol)
        if stock_data.get("status") == "success":
            stock_data["score"] = calculate_potential_score(stock_data)
    
    # 取得公司資訊
    company_info = get_company_info(symbol)
    
    # 生成推薦理由
    reasons = generate_recommendation_reasons(stock_data)
    
    # 取得新聞
    news = get_stock_news(symbol)
    
    # 組合完整資訊
    return {
        "symbol": symbol,
        "price_data": stock_data,
        "company_info": company_info,
        "recommendation_reasons": reasons,
        "news": news,
        "generated_at": datetime.now(TZ_TW).strftime("%Y-%m-%d %H:%M:%S")
    }


# 需要 timedelta
from datetime import timedelta
