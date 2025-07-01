#!/usr/bin/env python3
"""
Simple Telegram Bot Test
Test if the bot can receive and respond to commands
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple start command"""
    await update.message.reply_text("🤖 Bot is working! Use /test to test functionality.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple test command"""
    chat_id = str(update.message.chat_id)
    username = update.message.from_user.username or "Unknown"
    
    response = f"✅ <b>Test Successful!</b>\n\n"
    response += f"👤 User: @{username}\n"
    response += f"💬 Chat ID: {chat_id}\n"
    response += f"📱 Message: {update.message.text}\n\n"
    response += f"🎯 Bot is receiving and responding to commands correctly!"
    
    await update.message.reply_text(response, parse_mode='HTML')

async def add_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test add command functionality"""
    if not context.args:
        await update.message.reply_text("📋 Usage: /add_test 0x1234...5678:TestLabel")
        return
    
    arg = " ".join(context.args)
    
    if ":" in arg:
        address, label = arg.split(":", 1)
        address = address.strip()
        label = label.strip()
    else:
        address = arg.strip()
        label = f"{address[:6]}...{address[-4:]}"
    
    response = f"✅ <b>Add Test Successful!</b>\n\n"
    response += f"📍 Label: {label}\n"
    response += f"📊 Address: {address[:10]}...{address[-8:]}\n"
    response += f"🔗 Full Address: <code>{address}</code>\n\n"
    response += f"⚡ This would be added to tracking in the real system!"
    
    await update.message.reply_text(response, parse_mode='HTML')

async def main():
    """Main function to test the bot"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ No TELEGRAM_BOT_TOKEN found in .env file")
        return
    
    print("🤖 Starting simple Telegram bot test...")
    print(f"🔑 Using bot token: {bot_token[:10]}...")
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("add_test", add_test))
    
    try:
        # Initialize and start
        await application.initialize()
        await application.start()
        
        # Test connection
        bot_info = await application.bot.get_me()
        print(f"✅ Connected as: @{bot_info.username}")
        print(f"📱 Bot ID: {bot_info.id}")
        
        # Start polling
        print("🔄 Starting polling...")
        await application.updater.start_polling(
            drop_pending_updates=True,
            timeout=30
        )
        
        print("✅ Bot is running! Try these commands in Telegram:")
        print("   /start - Basic test")
        print("   /test - Detailed test with your info")
        print("   /add_test 0x1234:TestWhale - Test add functionality")
        print()
        print("Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n📴 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if application.updater.running:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main()) 