"""
統一日誌模組
提供結構化日誌功能
"""

import logging
import sys
from datetime import datetime
from typing import Any
import json


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 加入額外資訊
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # 加入錯誤資訊
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColorFormatter(logging.Formatter):
    """彩色終端格式化器（開發用）"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    取得 Logger 實例
    
    Args:
        name: Logger 名稱（通常使用 __name__）
        level: 日誌等級
    
    Returns:
        Logger 實例
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console Handler（彩色輸出）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColorFormatter(
        fmt="%(asctime)s │ %(levelname)-18s │ %(name)s │ %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(console_handler)
    
    return logger


# 預設 Logger
app_logger = get_logger("stock_app")


def log_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    """記錄 API 請求"""
    app_logger.info(
        f"{method} {path} → {status_code} ({duration_ms:.0f}ms)"
    )


def log_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """記錄錯誤"""
    app_logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        extra={"context": context} if context else {},
        exc_info=True
    )
