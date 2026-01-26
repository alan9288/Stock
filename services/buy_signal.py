"""
買入信號服務 - 強化財報分析版
提供智能加倉建議：建議買入價、建議加碼金額、買入分數
包含智能快取機制：基於財報公布日期自動過期
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
import time


# ==========================================
# 智能快取：基於財報日期過期
# ==========================================
class SmartFundamentalsCache:
    """
    智能財報快取
    - 每支股票的快取過期時間 = 下次財報公布日期
    - 若無法取得財報日期，預設 7 天過期
    - 最大儲存 500 支股票
    """
    
    MAX_ITEMS = 500
    DEFAULT_TTL_DAYS = 7
    
    def __init__(self):
        self._cache = {}  # {symbol: {"data": {...}, "expires_at": datetime}}
        self._lock = Lock()
    
    def get(self, symbol: str) -> Optional[Dict]:
        """取得快取資料，若過期則返回 None"""
        with self._lock:
            if symbol not in self._cache:
                return None
            
            entry = self._cache[symbol]
            expires_at = entry.get("expires_at")
            
            # 檢查是否過期
            if expires_at and datetime.now() > expires_at:
                del self._cache[symbol]
                print(f"[Cache] {symbol} 快取已過期，需重新取得")
                return None
            
            print(f"[Cache] {symbol} 從快取取得資料")
            data = entry["data"].copy()
            data["from_cache"] = True
            return data
    
    def set(self, symbol: str, data: Dict, earnings_date: Optional[datetime] = None):
        """儲存快取資料"""
        with self._lock:
            # 超過上限，清除最舊的
            if len(self._cache) >= self.MAX_ITEMS:
                oldest = min(self._cache.keys(), 
                           key=lambda k: self._cache[k].get("cached_at", 0))
                del self._cache[oldest]
                print(f"[Cache] 快取已滿，清除 {oldest}")
            
            # 決定過期時間
            if earnings_date and earnings_date > datetime.now():
                expires_at = earnings_date
            else:
                # 無法取得財報日期，預設 7 天
                expires_at = datetime.now() + timedelta(days=self.DEFAULT_TTL_DAYS)
            
            self._cache[symbol] = {
                "data": data,
                "expires_at": expires_at,
                "cached_at": datetime.now()
            }
            print(f"[Cache] {symbol} 已快取，過期時間: {expires_at.strftime('%Y-%m-%d')}")
    
    def clear(self):
        """清除所有快取"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict:
        """取得快取統計"""
        with self._lock:
            return {
                "count": len(self._cache),
                "symbols": list(self._cache.keys())
            }


# 全域快取實例
fundamentals_cache = SmartFundamentalsCache()


@dataclass
class HoldingData:
    """持股資料"""
    symbol: str
    market: str  # TW 或 US
    current_price: float
    avg_cost: float
    total_cost: float
    total_quantity: float


def get_fundamentals(symbol: str, market: str) -> Dict[str, Any]:
    """
    從 yfinance 取得完整財報資料（含智能快取）
    
    Args:
        symbol: 股票代號
        market: 市場 (TW/US)
    
    Returns:
        財報資料字典，包含 earnings_date
    """
    cache_key = f"{market}:{symbol}"
    
    # 1. 檢查快取
    cached = fundamentals_cache.get(cache_key)
    if cached:
        return cached
    
    # 2. 從 yfinance 取得資料
    try:
        # 處理台股後綴
        ticker_symbol = symbol if symbol.endswith(".TW") else (f"{symbol}.TW" if market == "TW" else symbol)
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 3. 取得下次財報日期
        earnings_date = None
        try:
            calendar = ticker.calendar
            if calendar is not None and not calendar.empty:
                # calendar 可能是 DataFrame 或 dict
                if hasattr(calendar, 'iloc'):
                    # DataFrame 格式
                    if 'Earnings Date' in calendar.columns:
                        ed = calendar['Earnings Date'].iloc[0]
                        if pd.notna(ed):
                            earnings_date = pd.to_datetime(ed).to_pydatetime()
                elif isinstance(calendar, dict):
                    ed = calendar.get('Earnings Date')
                    if ed:
                        earnings_date = datetime.fromisoformat(str(ed[0])) if isinstance(ed, list) else datetime.fromisoformat(str(ed))
        except Exception as e:
            print(f"[BuySignal] 取得 {symbol} 財報日期失敗: {e}")
        
        result = {
            # 估值指標
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "low_52w": info.get("fiftyTwoWeekLow"),
            "high_52w": info.get("fiftyTwoWeekHigh"),
            
            # 獲利指標
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "gross_margins": info.get("grossMargins"),
            "operating_margins": info.get("operatingMargins"),
            "profit_margins": info.get("profitMargins"),
            
            # 成長指標
            "earnings_growth": info.get("earningsGrowth"),
            "revenue_growth": info.get("revenueGrowth"),
            
            # 安全指標
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            
            # 股息指標
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            
            # 其他
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "name": info.get("shortName") or info.get("longName"),
            
            # 財報日期
            "earnings_date": earnings_date.isoformat() if earnings_date else None,
            "from_cache": False
        }
        
        # 4. 存入快取
        fundamentals_cache.set(cache_key, result, earnings_date)
        
        return result
    except Exception as e:
        print(f"[BuySignal] 取得 {symbol} 財報資料失敗: {e}")
        return {}


def calculate_buy_score(holding: HoldingData, fundamentals: Dict[str, Any]) -> int:
    """
    計算買入分數 (0-100)
    
    指標權重：
    - P/E Ratio: 15%
    - P/B Ratio: 10%
    - ROE: 15%
    - 毛利率: 10%
    - EPS 成長: 15%
    - 營收成長: 10%
    - 負債比率: 10%
    - 現價 vs 成本: 10%
    - 殖利率: 5%
    """
    score = 0
    
    # 1. P/E 評分 (15分)
    pe = fundamentals.get("pe_ratio")
    if pe and pe > 0:
        if pe < 10:      score += 15
        elif pe < 15:    score += 12
        elif pe < 20:    score += 9
        elif pe < 30:    score += 6
        else:            score += 3
    else:
        score += 7  # 無資料給中間分
    
    # 2. P/B 評分 (10分)
    pb = fundamentals.get("pb_ratio")
    if pb and pb > 0:
        if pb < 1:       score += 10
        elif pb < 2:     score += 8
        elif pb < 3:     score += 5
        else:            score += 2
    else:
        score += 5
    
    # 3. ROE 評分 (15分)
    roe = fundamentals.get("roe")
    if roe is not None:
        if roe > 0.20:   score += 15  # ROE > 20% 優秀
        elif roe > 0.15: score += 12
        elif roe > 0.10: score += 9
        elif roe > 0.05: score += 6
        else:            score += 3
    else:
        score += 7
    
    # 4. 毛利率評分 (10分)
    gross = fundamentals.get("gross_margins")
    if gross is not None:
        if gross > 0.50:   score += 10  # 毛利率 > 50% 優秀
        elif gross > 0.35: score += 8
        elif gross > 0.20: score += 5
        else:              score += 2
    else:
        score += 5
    
    # 5. EPS 成長評分 (15分)
    eps_growth = fundamentals.get("earnings_growth")
    if eps_growth is not None:
        if eps_growth > 0.20:   score += 15
        elif eps_growth > 0.10: score += 12
        elif eps_growth > 0:    score += 9
        elif eps_growth > -0.1: score += 4
        else:                   score += 0
    else:
        score += 7
    
    # 6. 營收成長評分 (10分)
    rev_growth = fundamentals.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth > 0.20:   score += 10
        elif rev_growth > 0.10: score += 8
        elif rev_growth > 0:    score += 5
        else:                   score += 2
    else:
        score += 5
    
    # 7. 負債比率評分 (10分) - 負債比率越低越好
    debt = fundamentals.get("debt_to_equity")
    if debt is not None:
        if debt < 0.3:     score += 10  # 低負債
        elif debt < 0.5:   score += 8
        elif debt < 1.0:   score += 5
        elif debt < 2.0:   score += 2
        else:              score += 0   # 高槓桿風險
    else:
        score += 5
    
    # 8. 現價 vs 成本 (10分)
    if holding.current_price and holding.avg_cost and holding.avg_cost > 0:
        ratio = holding.current_price / holding.avg_cost
        if ratio < 0.8:      score += 10  # 虧損 > 20%
        elif ratio < 0.95:   score += 8
        elif ratio < 1.05:   score += 5
        elif ratio < 1.2:    score += 3
        else:                score += 1
    else:
        score += 5
    
    # 9. 殖利率評分 (5分)
    div_yield = fundamentals.get("dividend_yield")
    if div_yield is not None:
        if div_yield > 0.05:   score += 5  # 殖利率 > 5%
        elif div_yield > 0.03: score += 4
        elif div_yield > 0.01: score += 2
        else:                  score += 1
    else:
        score += 2
    
    return score


def get_buy_rating(score: int) -> tuple:
    """
    根據分數回傳評級和顏色
    
    Returns:
        (評級文字, emoji)
    """
    if score >= 80:
        return ("極佳", "🟢")
    elif score >= 60:
        return ("良好", "🟡")
    elif score >= 40:
        return ("普通", "🔵")
    elif score >= 20:
        return ("偏弱", "🟠")
    else:
        return ("差", "🔴")


def calculate_suggested_price(holding: HoldingData, fundamentals: Dict[str, Any]) -> float:
    """
    計算建議買入價
    
    策略：價值型投資 + 技術支撐
    """
    current_price = holding.current_price
    avg_cost = holding.avg_cost
    low_52w = fundamentals.get("low_52w")
    pe_ratio = fundamentals.get("pe_ratio")
    
    # 1. 基於成本的目標價（攤平成本策略）
    if current_price < avg_cost:
        # 已經虧損，在現價基礎上找支撐
        cost_target = current_price * 0.97  # 再跌 3% 進場
    else:
        # 已經獲利，在成本下方設置買點
        cost_target = avg_cost * 0.95  # 成本下 5%
    
    # 2. 基於 P/E 的合理價
    if pe_ratio and pe_ratio > 0:
        if pe_ratio > 30:      # 高估值
            pe_discount = 0.85  # 需跌 15%
        elif pe_ratio > 20:    # 合理偏高
            pe_discount = 0.92  # 需跌 8%
        elif pe_ratio > 15:    # 合理
            pe_discount = 0.97  # 跌 3% 就可買
        else:                  # 低估值
            pe_discount = 1.0   # 現價即可
        pe_target = current_price * pe_discount
    else:
        pe_target = current_price  # 無 P/E 資料
    
    # 3. 基於 52 週低點的支撐價
    if low_52w:
        support_target = low_52w * 1.03  # 低點上方 3%
    else:
        support_target = current_price * 0.9
    
    # 最終建議價 = 三者取最高（不要過於保守）
    suggested_price = max(cost_target, pe_target, support_target)
    
    return round(suggested_price, 2)


def calculate_suggested_amount(holding: HoldingData, score: int) -> float:
    """
    計算建議加碼金額
    
    基於：持倉成本 × 加碼比例（由買入分數決定）
    """
    total_cost = holding.total_cost
    
    # 根據買入分數決定加碼比例
    if score >= 80:
        ratio = 0.30    # 超優質，加碼 30%
    elif score >= 60:
        ratio = 0.20    # 優質，加碼 20%
    elif score >= 40:
        ratio = 0.10    # 普通，加碼 10%
    else:
        ratio = 0.00    # 不建議加碼
    
    suggested = total_cost * ratio
    
    # 設定最小/最大金額
    if suggested > 0:
        if holding.market == "TW":
            suggested = max(suggested, 1000)    # 台股最少 NT$1,000
            suggested = min(suggested, 100000)  # 最多 NT$100,000
        else:
            suggested = max(suggested, 100)     # 美股最少 $100
            suggested = min(suggested, 10000)   # 最多 $10,000
    
    return round(suggested, 2)


def get_buy_signal(symbol: str, market: str, current_price: float, 
                   avg_cost: float, total_cost: float, total_quantity: float) -> Dict[str, Any]:
    """
    整合所有計算，回傳完整買入信號
    
    Args:
        symbol: 股票代號
        market: 市場 (TW/US)
        current_price: 現價
        avg_cost: 平均成本
        total_cost: 總成本
        total_quantity: 總股數
    
    Returns:
        買入信號資料
    """
    holding = HoldingData(
        symbol=symbol,
        market=market,
        current_price=current_price,
        avg_cost=avg_cost,
        total_cost=total_cost,
        total_quantity=total_quantity
    )
    
    # 取得財報資料
    fundamentals = get_fundamentals(symbol, market)
    
    # 計算買入分數
    buy_score = calculate_buy_score(holding, fundamentals)
    rating_text, rating_emoji = get_buy_rating(buy_score)
    
    # 計算建議價格
    suggested_price = calculate_suggested_price(holding, fundamentals)
    
    # 判斷買入狀態
    if current_price <= suggested_price:
        buy_status = "🟢 現在買"
    elif current_price <= suggested_price * 1.05:
        buy_status = "🟡 即將到達"
    else:
        currency = "NT$" if market == "TW" else "$"
        buy_status = f"⏳ 等待 {currency}{suggested_price:,.0f}"
    
    # 計算建議加碼金額
    suggested_amount = calculate_suggested_amount(holding, buy_score)
    
    return {
        "buy_score": buy_score,
        "buy_rating": f"{rating_emoji} {rating_text}",
        "buy_status": buy_status,
        "suggested_price": suggested_price,
        "suggested_amount": suggested_amount,
        "fundamentals": {
            "pe_ratio": fundamentals.get("pe_ratio"),
            "pb_ratio": fundamentals.get("pb_ratio"),
            "roe": fundamentals.get("roe"),
            "gross_margins": fundamentals.get("gross_margins"),
            "earnings_growth": fundamentals.get("earnings_growth"),
            "revenue_growth": fundamentals.get("revenue_growth"),
            "debt_to_equity": fundamentals.get("debt_to_equity"),
            "dividend_yield": fundamentals.get("dividend_yield"),
            "low_52w": fundamentals.get("low_52w"),
            "high_52w": fundamentals.get("high_52w"),
        },
        "earnings_date": fundamentals.get("earnings_date"),
        "from_cache": fundamentals.get("from_cache", False)
    }


# ==========================================
# 測試用函數
# ==========================================

def test_buy_signal(symbol: str, market: str = "US"):
    """
    測試買入信號（可直接執行）
    
    使用範例：
        python -c "from services.buy_signal import test_buy_signal; test_buy_signal('AAPL')"
    """
    print(f"\n{'='*60}")
    print(f"📊 買入信號分析: {symbol} ({market})")
    print(f"{'='*60}")
    
    # 取得即時報價
    ticker_symbol = f"{symbol}.TW" if market == "TW" and not symbol.endswith(".TW") else symbol
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
    
    # 模擬持股資料
    avg_cost = current_price * 1.1  # 假設成本高於現價 10%
    total_cost = avg_cost * 100
    total_quantity = 100
    
    # 計算買入信號
    signal = get_buy_signal(
        symbol=symbol, 
        market=market,
        current_price=current_price,
        avg_cost=avg_cost,
        total_cost=total_cost,
        total_quantity=total_quantity
    )
    
    print(f"\n📈 現價: ${current_price:,.2f}")
    print(f"💰 假設成本: ${avg_cost:,.2f} (模擬虧損)")
    print(f"\n🎯 買入分數: {signal['buy_score']}/100 {signal['buy_rating']}")
    print(f"📍 買入狀態: {signal['buy_status']}")
    print(f"💵 建議買價: ${signal['suggested_price']:,.2f}")
    print(f"💰 建議加碼: ${signal['suggested_amount']:,.2f}")
    
    print("\n📊 財報指標:")
    fund = signal['fundamentals']
    
    pe = fund.get('pe_ratio')
    pb = fund.get('pb_ratio')
    roe = fund.get('roe')
    gross = fund.get('gross_margins')
    eps_g = fund.get('earnings_growth')
    rev_g = fund.get('revenue_growth')
    debt = fund.get('debt_to_equity')
    div_y = fund.get('dividend_yield')
    low52 = fund.get('low_52w')
    high52 = fund.get('high_52w')
    
    print(f"   P/E Ratio:     {pe:.2f}" if pe else "   P/E Ratio:     N/A")
    print(f"   P/B Ratio:     {pb:.2f}" if pb else "   P/B Ratio:     N/A")
    print(f"   ROE:           {roe*100:.1f}%" if roe else "   ROE:           N/A")
    print(f"   毛利率:        {gross*100:.1f}%" if gross else "   毛利率:        N/A")
    print(f"   EPS 成長:      {eps_g*100:.1f}%" if eps_g else "   EPS 成長:      N/A")
    print(f"   營收成長:      {rev_g*100:.1f}%" if rev_g else "   營收成長:      N/A")
    print(f"   負債比率:      {debt:.2f}" if debt is not None else "   負債比率:      N/A")
    print(f"   殖利率:        {div_y*100:.2f}%" if div_y else "   殖利率:        N/A")
    print(f"   52週低點:      ${low52:,.2f}" if low52 else "   52週低點:      N/A")
    print(f"   52週高點:      ${high52:,.2f}" if high52 else "   52週高點:      N/A")
    
    return signal


if __name__ == "__main__":
    # 測試美股
    test_buy_signal("AAPL", "US")
    test_buy_signal("MSFT", "US")
    
    # 測試台股
    test_buy_signal("2330.TW", "TW")
