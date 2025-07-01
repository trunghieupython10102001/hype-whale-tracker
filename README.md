# 🐋 Hyperliquid Whale Tracker

A Python tool to monitor and track position changes for multiple wallet addresses on Hyperliquid DEX. Get real-time notifications when whales open, close, or modify their positions.

## ✨ Features

- **Multi-Address Monitoring**: Track unlimited wallet addresses simultaneously
- **Real-Time Position Tracking**: Monitor opens, closes, increases, and decreases
- **Smart Filtering**: Configurable minimum position sizes and change thresholds
- **Persistent Storage**: Saves position data to resume tracking after restarts
- **Rich Logging**: Console output and file logging with timestamps
- **Clean Output**: Emoji-rich, easy-to-read position change notifications
- **Telegram Alerts**: Real-time notifications via Telegram bot
- **Testnet Support**: Test on Hyperliquid testnet before using mainnet
- **Error Handling**: Robust error handling with automatic retry logic

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Addresses

Edit `config.py` and add the wallet addresses you want to track:

```python
TRACKED_ADDRESSES: List[str] = [
    "0xcd5051944f780a621ee62e39e493c489668acf4d",  # Example address
    "0x1234567890123456789012345678901234567890",  # Add your addresses here
    "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
]
```

### 3. Run the Tracker

```bash
# Main whale tracker
python main.py

# Optional: Run command handler for Telegram commands (separate terminal)
python telegram_command_handler.py
```

## 📱 Telegram Setup (Optional)

Get instant whale alerts on your phone!

### 1. Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` to create a new bot
3. Choose a name and username for your bot
4. Copy the **bot token** (looks like `123456789:ABCdefGhIJKlmnoPQRstu-vwxyz`)

### 2. Get Your Chat ID

1. Start a chat with your new bot
2. Send any message to the bot
3. Visit this URL (replace `BOT_TOKEN` with your actual token):
   ```
   https://api.telegram.org/botBOT_TOKEN/getUpdates
   ```
4. Look for `"chat":{"id":YOUR_CHAT_ID}` and copy the chat ID

### 3. Configure Environment

Create a `.env` file (copy from `env_example.txt`):

```bash
ENABLE_TELEGRAM_ALERTS=true
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmnoPQRstu-vwxyz
TELEGRAM_CHAT_ID=123456789
```

### 4. Test Your Setup

```bash
python3 utils.py test-telegram
```

You should receive a test message in Telegram!

## 📋 Configuration

### Basic Configuration (config.py)

Key settings you can customize:

```python
# Addresses to monitor
TRACKED_ADDRESSES = ["0x...", "0x..."]

# How often to check for changes (seconds)
POLLING_INTERVAL = 30

# Minimum position size to track (USD)
MIN_POSITION_SIZE = 1000

# Minimum change amount to notify (USD)
MIN_CHANGE_THRESHOLD = 500

# Use testnet instead of mainnet
USE_TESTNET = False
```

### Environment Variables (Optional)

Create a `.env` file (copy from `env_example.txt`):

```bash
USE_TESTNET=false
POLLING_INTERVAL=30
MIN_POSITION_SIZE=1000
MIN_CHANGE_THRESHOLD=500
```

### Address Labels

Add friendly names for addresses in `config.py`:

```python
@classmethod
def get_address_labels(cls) -> Dict[str, str]:
    return {
        "0xcd5051944f780a621ee62e39e493c489668acf4d": "Whale #1",
        "0x1234567890123456789012345678901234567890": "DeFi Fund",
        "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd": "Market Maker",
    }
```

## 📊 Sample Output

```
============================================================
🐋 HYPERLIQUID WHALE TRACKER
============================================================
📡 API URL: https://api.hyperliquid.xyz
⏱️  Polling Interval: 30 seconds
💰 Min Position Size: $1,000
📊 Min Change Threshold: $500
📍 Tracking 3 addresses:
   1. Whale #1 (0xcd50...4d)
   2. DeFi Fund (0x1234...90)
   3. Market Maker (0xabcd...cd)
============================================================
🔍 Monitoring started... Press Ctrl+C to stop
============================================================

2024-01-15 10:30:45 - 🟢 Whale #1 OPENED BTC LONG $50,000.00 @ $42,500
2024-01-15 10:35:12 - 📈 DeFi Fund INCREASED ETH LONG +$25,000.00 Total: $175,000.00
2024-01-15 10:42:33 - 🔴 Market Maker CLOSED SOL SHORT $15,000.00 PnL: +$2,150.00
```

### 📱 Telegram Notifications

Your Telegram bot will send individual alerts for position changes:

```
📈 James Wynn
INCREASED BTC LONG
+$25,000.00
Total: $1,394,810.92
🕐 10:35:12
📊 View on Hyperdash

🔴 DeFi Fund
CLOSED ETH SHORT
$50,000.00
PnL: +$2,150.00
🕐 10:42:33
📊 View on Hyperdash
```

**Note:** Opening positions are NOT sent to avoid startup spam. Only actual changes (increases, decreases, closures) trigger alerts.

### 🤖 Telegram Commands

Add new addresses dynamically via Telegram:

```
/add 0x1234567890123456789012345678901234567890:My Whale
/add 0xabcdefabcdefabcdefabcdefabcdefabcdefabcd
/list
/help
```

**Setup:**
1. Run the command handler: `python3 telegram_command_handler.py`
2. Use commands in your Telegram chat with the bot
3. Addresses are validated and stored persistently

## 🏗️ Project Structure

```
whale-tracker/
├── main.py              # Main application entry point
├── position_tracker.py  # Core tracking logic
├── telegram_bot.py     # Telegram notifications
├── config.py           # Configuration settings
├── utils.py            # Utility functions and testing
├── requirements.txt    # Python dependencies
├── env_example.txt     # Environment variables template
├── README.md          # This file
├── data/              # Position data storage (created automatically)
│   └── positions.json # Persistent position data
└── whale_tracker.log  # Log file (created automatically)
```

## 🔧 Advanced Usage

### Custom Polling Interval

Adjust how often the tracker checks for changes:

```python
# Check every 15 seconds (be mindful of rate limits)
POLLING_INTERVAL = 15

# Check every 2 minutes for less frequent updates
POLLING_INTERVAL = 120
```

### Position Size Filtering

Control which positions get tracked:

```python
# Only track positions worth $5000 or more
MIN_POSITION_SIZE = 5000

# Track all positions (be careful with spam)
MIN_POSITION_SIZE = 0
```

### Change Sensitivity

Set how sensitive the tracker is to position changes:

```python
# Only notify for changes >= $1000
MIN_CHANGE_THRESHOLD = 1000

# Notify for any change >= $100
MIN_CHANGE_THRESHOLD = 100
```

### Testnet Mode

Test the tracker safely on Hyperliquid testnet:

```python
USE_TESTNET = True
```

Or via environment variable:
```bash
USE_TESTNET=true python main.py
```

## 📝 Logging

The tracker provides comprehensive logging:

- **Console Output**: Real-time position change notifications
- **File Logging**: All events saved to `whale_tracker.log`
- **Log Levels**: Configurable (DEBUG, INFO, WARNING, ERROR)

## 💾 Data Persistence

Position data is automatically saved to `data/positions.json`:

- Resumes tracking after restarts
- Prevents duplicate notifications
- Maintains position history
- JSON format for easy analysis

## 🛠️ Troubleshooting

### Common Issues

**"No addresses configured for tracking"**
- Add wallet addresses to `TRACKED_ADDRESSES` in `config.py`

**API Connection Errors**
- Check your internet connection
- Verify the API URL is correct
- Try using testnet first with `USE_TESTNET=True`

**Rate Limiting**
- Increase `POLLING_INTERVAL` (recommended: 30+ seconds)
- Reduce number of tracked addresses

**No Position Changes Detected**
- Verify addresses have active positions
- Check if position changes meet your thresholds
- Lower `MIN_POSITION_SIZE` and `MIN_CHANGE_THRESHOLD` for testing

**Telegram Not Working**
- Check bot token and chat ID are correct
- Run `python3 utils.py test-telegram`
- Ensure you've started a chat with your bot
- Verify bot isn't blocked or deleted

### Debug Mode

Enable debug logging for troubleshooting:

```python
LOG_LEVEL = "DEBUG"
```

## 📚 API Documentation

This tracker uses the official Hyperliquid Python SDK:
- [Hyperliquid API Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)
- [Python SDK GitHub](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)

## ⚠️ Important Notes

- **Rate Limits**: Respect Hyperliquid's rate limits (recommended: 30+ second intervals)
- **No Trading**: This tool is read-only and only monitors positions
- **Public Data**: Only tracks publicly visible position data
- **Testnet First**: Test with testnet before using on mainnet
- **Resource Usage**: Monitor CPU/memory usage with many addresses

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- WebSocket support for real-time updates
- Discord/Telegram notifications
- Web dashboard interface
- Additional filtering options
- Performance optimizations

## 📄 License

This project is open source. Use responsibly and respect Hyperliquid's terms of service.

## 🔗 Links

- [Hyperliquid Exchange](https://app.hyperliquid.xyz/)
- [Hyperliquid Docs](https://hyperliquid.gitbook.io/)
- [Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)

---

**Happy whale watching! 🐋📊** 