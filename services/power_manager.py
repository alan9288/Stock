"""
電源管理模組 - 低耗電模式
根據市場開市狀態自動調整輪詢頻率
"""

from datetime import datetime, time as dtime
import pytz
from typing import Literal

# 時區設定
TZ_TW = pytz.timezone("Asia/Taipei")
TZ_US = pytz.timezone("America/New_York")

# 輪詢間隔（秒）
POLLING_NORMAL = 30       # 開市中
POLLING_LOW = 1800        # 休市（30 分鐘）
POLLING_SLEEP = 0         # 週末（完全停止）

# 開市時間定義
MARKET_HOURS = {
    "TW": {
        "open": dtime(9, 0),
        "close": dtime(13, 30),
        "timezone": TZ_TW
    },
    "US": {
        "open": dtime(9, 30),
        "close": dtime(16, 0),
        "timezone": TZ_US
    }
}


def is_weekday() -> bool:
    """判斷今天是否為工作日（週一到週五）"""
    now = datetime.now(TZ_TW)
    return now.weekday() < 5  # 0=週一, 4=週五


def is_market_open(market: str = "TW") -> bool:
    """
    判斷指定市場是否開市
    
    Args:
        market: "TW" 或 "US"
    
    Returns:
        bool: 是否開市中
    """
    if market not in MARKET_HOURS:
        return False
    
    hours = MARKET_HOURS[market]
    now = datetime.now(hours["timezone"])
    
    # 週末不開市
    if now.weekday() >= 5:
        return False
    
    # 檢查是否在開市時間內
    current_time = now.time()
    return hours["open"] <= current_time <= hours["close"]


def get_power_mode() -> Literal["normal", "low", "sleep"]:
    """
    取得當前電源模式
    
    Returns:
        - "normal": 有市場開市中，正常輪詢
        - "low": 休市但是工作日，低頻率輪詢
        - "sleep": 週末，完全停止輪詢
    """
    # 檢查任一市場是否開市
    if is_market_open("TW") or is_market_open("US"):
        return "normal"
    
    # 工作日但休市
    if is_weekday():
        return "low"
    
    # 週末
    return "sleep"


def get_polling_interval() -> int:
    """
    取得當前輪詢間隔（秒）
    
    Returns:
        int: 輪詢間隔秒數，0 表示停止輪詢
    """
    mode = get_power_mode()
    
    if mode == "normal":
        return POLLING_NORMAL
    elif mode == "low":
        return POLLING_LOW
    else:
        return POLLING_SLEEP


def get_power_status() -> dict:
    """
    取得完整的電源狀態資訊
    
    Returns:
        dict: 包含模式、輪詢間隔、各市場狀態
    """
    mode = get_power_mode()
    interval = get_polling_interval()
    
    return {
        "mode": mode,
        "mode_display": {
            "normal": "🟢 正常模式",
            "low": "🟡 省電模式", 
            "sleep": "🔴 休眠模式"
        }.get(mode, "❓ 未知"),
        "polling_interval": interval,
        "polling_interval_display": f"{interval}秒" if interval > 0 else "已停止",
        "markets": {
            "TW": {
                "is_open": is_market_open("TW"),
                "status": "開市中" if is_market_open("TW") else "休市"
            },
            "US": {
                "is_open": is_market_open("US"),
                "status": "開市中" if is_market_open("US") else "休市"
            }
        },
        "is_weekday": is_weekday()
    }
