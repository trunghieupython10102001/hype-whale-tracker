#!/usr/bin/env python3
"""
Standalone Telegram Command Handler for Whale Tracker
Run this alongside the main tracker to handle /add and /list commands
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram_bot import TelegramNotifier
from config import Config


class WhaleTrackerCommandHandler:
    """Handles Telegram commands for the whale tracker"""
    
    def __init__(self):
        self.config = Config
        self.logger = logging.getLogger('CommandHandler')
        self.notifier = TelegramNotifier()
        self.application = None
        
        # Set up logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
    
    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command"""
        await self.notifier.handle_add_command(update, context)
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command"""
        await self.notifier.handle_list_command(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if str(update.message.chat_id) != self.config.TELEGRAM_CHAT_ID:
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        help_text = (
            "🐋 <b>Whale Tracker Commands</b>\n\n"
            "📌 <b>/add address:label</b>\n"
            "   Add new address with custom label\n"
            "   Example: /add 0x1234...5678:My Whale\n\n"
            "📌 <b>/add address</b>\n"
            "   Add new address with auto-generated label\n"
            "   Example: /add 0x1234...5678\n\n"
            "📊 <b>/list</b>\n"
            "   Show all tracked addresses\n\n"
            "❓ <b>/help</b>\n"
            "   Show this help message\n\n"
            "📝 <b>Notes:</b>\n"
            "• Addresses must be 42 characters long\n"
            "• Addresses must start with 0x\n"
            "• Only actual position changes are alerted\n"
            "• Opening positions are skipped to avoid spam"
        )
        
        await update.message.reply_text(help_text)
    
    async def start_command_handler(self):
        """Start the command handler"""
        try:
            if not self.config.TELEGRAM_BOT_TOKEN:
                self.logger.error("Telegram bot token not configured")
                return
            
            # Create application
            self.application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("add", self.add_command))
            self.application.add_handler(CommandHandler("list", self.list_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("start", self.help_command))
            
            self.logger.info("🤖 Telegram command handler started")
            self.logger.info("📋 Available commands: /add, /list, /help")
            self.logger.info("💡 Use /help in Telegram for usage instructions")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Command handler stopped by user")
        except Exception as e:
            self.logger.error(f"Error in command handler: {e}")
        finally:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()


async def main():
    """Main function"""
    print("🤖 Starting Telegram Command Handler for Whale Tracker")
    print("=" * 60)
    print("📋 This handler enables these Telegram commands:")
    print("   /add address:label - Add new address with label")
    print("   /add address - Add new address")
    print("   /list - Show tracked addresses")
    print("   /help - Show help message")
    print("=" * 60)
    print("💡 Run this alongside your main whale tracker")
    print("🔄 Starting command handler...")
    
    handler = WhaleTrackerCommandHandler()
    await handler.start_command_handler()


if __name__ == "__main__":
    asyncio.run(main()) 