import os
import json
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = os.getenv('BOT_CONFIG_PATH', 'bot_config.json')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

_config = load_config()

# Binance API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Trading Parameters (from bot_config.json)
TRADING_PAIRS = _config.get('TRADING_PAIRS', ['ETHUSDT'])
LEVERAGE = _config.get('LEVERAGE', 3)
TRAILING_STOP_PERCENTAGE = _config.get('TRAILING_STOP_PERCENTAGE', 1.0)
TAKE_PROFIT_PERCENTAGE = _config.get('TAKE_PROFIT_PERCENTAGE', 2.0)
MIN_NOTIONAL = _config.get('MIN_NOTIONAL', 20.0)
MIN_BALANCE_THRESHOLD = _config.get('MIN_BALANCE_THRESHOLD', 100.0)
POSITION_SIZE_BUFFER = _config.get('POSITION_SIZE_BUFFER', 0.90)
SMALL_ACCOUNT_POSITION_LIMIT = _config.get('SMALL_ACCOUNT_POSITION_LIMIT', 0.50)

# Notification Settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')  # Discord webhook URL for notifications

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join("logs", "trading_bot.log") 