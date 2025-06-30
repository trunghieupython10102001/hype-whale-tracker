# 📱 Telegram Bot Setup Guide

Follow these steps to receive whale alerts directly on your phone via Telegram!

## Step 1: Create Your Bot

1. Open Telegram on your phone or computer
2. Search for `@BotFather` or click [here](https://t.me/botfather)
3. Start a chat with BotFather
4. Send `/newbot` command
5. Choose a name for your bot (e.g., "My Whale Tracker")
6. Choose a username (e.g., "my_whale_tracker_bot")
7. **Save the bot token** (it looks like `123456789:ABCdefGhIJKlmnoPQRstu-vwxyz`)

## Step 2: Get Your Chat ID

1. Find your new bot in Telegram and start a chat with it
2. Send any message to your bot (e.g., "hello")
3. Open your web browser and go to:
   ```
   https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getUpdates
   ```
   Replace `{YOUR_BOT_TOKEN}` with your actual bot token
4. Look for something like:
   ```json
   "chat":{"id":123456789,"first_name":"Your Name"}
   ```
5. **Save the chat ID** (the number, e.g., `123456789`)

## Step 3: Configure the Tracker

1. Copy the example environment file:
   ```bash
   cp env_example.txt .env
   ```

2. Edit the `.env` file with your favorite text editor:
   ```bash
   nano .env
   ```

3. Update these lines with your actual values:
   ```
   ENABLE_TELEGRAM_ALERTS=true
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmnoPQRstu-vwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

## Step 4: Test Your Setup

Run the test command:
```bash
python3 utils.py test-telegram
```

You should see:
```
✅ Bot token: 123456789:...
✅ Chat ID: 123456789
✅ Telegram bot test successful!
   Check your Telegram chat for the test message
```

**Check your Telegram** - you should receive a test message from your bot!

## Step 5: Start Monitoring

Now run the whale tracker:
```bash
python3 main.py
```

You'll receive:
- 🚀 Startup notification when the tracker begins
- 🟢🔴📈📉 Real-time position change alerts
- ⚠️ Error notifications if something goes wrong
- 🛑 Shutdown notification when stopped

## Troubleshooting

**❌ "Telegram bot test failed"**
- Double-check your bot token
- Make sure you've sent at least one message to your bot
- Verify your chat ID is correct

**❌ "Bot token not configured"**
- Make sure your `.env` file exists
- Check that `TELEGRAM_BOT_TOKEN` is set correctly
- No quotes needed around the token in `.env`

**❌ "Chat ID not configured"**
- Verify you followed Step 2 correctly
- The chat ID should be just numbers (positive or negative)
- Try sending another message to your bot and check the API again

**❌ Bot doesn't respond**
- Make sure the bot isn't blocked
- Check that the username is correct
- Try creating a new bot if needed

## Example Telegram Messages

Once set up, you'll receive alerts like:

```
🟢 James Wynn
OPENED BTC LONG  
$50,000.00 @ $42,500
🕐 14:30:45
```

```
🐋 Whale Activity Detected
📊 3 position changes

📍 James Wynn
  INCREASED ETH LONG
  +$25,000.00
  Total: $125,000.00
  🕐 14:35:12

📍 0x8af70...fa05
  CLOSED SOL SHORT
  $15,000.00
  PnL: +$2,150.00
  🕐 14:42:33
```

**You're all set! 🐋📱** 