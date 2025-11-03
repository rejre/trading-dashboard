import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path("/Users/belfort/gemini/StockTradingSystem")
DATA_DIR = BASE_DIR / "storage" / "stock_data"
LOG_DIR = BASE_DIR / "storage" / "logs"

# 创建必要的目录
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 交易时间配置
TRADING_HOURS = {
    "market_open": "09:15",
    "market_close": "15:00",
    "morning_start": "09:15",
    "morning_end": "11:30", 
    "afternoon_start": "13:00",
    "afternoon_end": "15:00"
}

# 天时裁决参数
MARKET_JUDGE_CONFIG = {
    'index_ma_days': 20,
    'volume_threshold': 800000000000,  # 8000亿
    'zt_profit_threshold': 1.5,
    'chain_height_threshold': 4
}