# Binance Futures Trading Bot

A robust trading bot for Binance Futures with trailing stop loss, multi-channel notifications, and comprehensive logging.

## Features

- Binance Futures trading integration
- Trailing Stop Loss implementation
- Multi-channel notifications (Telegram, Email, Discord)
- Comprehensive logging system
- Docker containerization
- Risk management and profit optimization

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Binance Futures account with API access
- Telegram bot token (optional)
- Gmail account for email notifications (optional)
- Discord server with webhook access (optional)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd bot-trade
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

3. Edit the `.env` file with your credentials:
- Add your Binance API key and secret
- Add your Telegram bot token and chat ID (optional)
- Add your Gmail credentials for email notifications (optional)
- Add your Discord webhook URL (optional)

### Setting up Discord Notifications

1. Create a new Discord server or use an existing one
2. Go to Server Settings > Integrations > Webhooks
3. Click "New Webhook"
4. Give it a name (e.g., "Trading Bot")
5. Select the channel where you want to receive notifications
6. Copy the Webhook URL
7. Add the Webhook URL to your `.env` file as `DISCORD_WEBHOOK_URL`

## Running with Docker Compose

1. Build and start the container:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f
```

3. Stop the container:
```bash
docker-compose down
```

## Running without Docker

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the bot:
```bash
python main.py
```

## Configuration

Edit `config.py` to customize:
- Trading pairs
- Leverage
- Position size
- Trailing stop percentage
- Take profit percentage
- Logging settings

## Configuration via bot_config.json

Trading parameters (symbols, leverage, trailing stop, etc.) are now set in `bot_config.json`.

Example `bot_config.json`:

```
{
  "TRADING_PAIRS": ["ETHUSDT", "BTCUSDT"],
  "LEVERAGE": 3,
  "TRAILING_STOP_PERCENTAGE": 1.0,
  "TAKE_PROFIT_PERCENTAGE": 2.0,
  "MIN_NOTIONAL": 20.0,
  "MIN_BALANCE_THRESHOLD": 100.0,
  "POSITION_SIZE_BUFFER": 0.90,
  "SMALL_ACCOUNT_POSITION_LIMIT": 0.50
}
```

- To change trading pairs, leverage, or other parameters, edit `bot_config.json` and restart the bot.
- You can set the config file path with the environment variable `BOT_CONFIG_PATH` if needed.

## Logging

Logs are stored in the `logs` directory with daily rotation and 7-day retention. When running with Docker Compose, logs are persisted in the `./logs` directory on your host machine.

## Notifications

The bot supports multiple notification channels:
- Telegram: Real-time trading updates
- Email: Detailed trade reports and error notifications
- Discord: Real-time trading updates with customizable webhook

## Risk Warning

Trading cryptocurrencies involves significant risk. This bot is provided as-is, without any guarantees of profit. Always test with small amounts first and monitor the bot's performance.

## License

MIT License # binance-treade-future
# binance-treade-future

## Web UI

The bot includes a web-based dashboard for monitoring and configuration:

### Accessing the Web UI
- **URL**: `http://your-server-ip:8501`
- **Default Port**: 8501

### Features
- **Dashboard**: Real-time bot status, active trades, and performance metrics
- **Configuration**: Easy modification of trading parameters without editing files
- **Logs**: View and search bot logs with statistics
- **Bot Control**: Start, stop, and restart the bot (when implemented)

### Starting the Web UI
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or run directly
streamlit run web_ui.py --server.port 8501 --server.address 0.0.0.0
```

### Web UI Configuration
- All configuration changes are saved to `bot_config.json`
- Changes require bot restart to take effect
- The UI provides validation and helpful tooltips
