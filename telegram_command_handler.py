#!/usr/bin/env python3
"""
Standalone Telegram Command Handler for Whale Tracker
Run this alongside the main tracker to handle /add and /list commands
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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
        """Handle /add command - available to everyone"""
        await self.notifier.handle_add_command(update, context)
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command with interactive buttons - available to everyone"""
        # Register user for broadcasts
        user = update.message.from_user
        self.notifier.add_user(user.id, user.username, user.first_name)
        
        # Get all tracked addresses
        all_tracked_addresses = self.notifier.get_all_tracked_addresses()
        
        if not all_tracked_addresses:
            await update.message.reply_text(
                "📊 No Tracked Addresses\n\n"
                "❌ You haven't added any addresses to track yet.\n\n"
                "💡 Use /add address:label or /add address to start tracking!\n\n"
                "📌 Examples:\n"
                "/add 0x1234567890123456789012345678901234567890:My Whale\n"
                "/add 0x1234567890123456789012345678901234567890 (auto-generates alias like 'Golden Eagle')"
            )
            return
        
        # Build message and inline keyboard
        message = "📊 Tracked Addresses\n\n"
        
        keyboards = []
        for i, address in enumerate(all_tracked_addresses, 1):
            # Get label for this address
            labels = self.notifier.get_all_address_labels()
            label = labels.get(address, f"{address[:6]}...{address[-4:]}")
            
            # Add address info to message
            message += f"📌 {label}\n"
            message += f"   📍 {address[:10]}...{address[-8:]}\n"
            message += f"   🔗 https://hyperdash.info/trader/{address}\n\n"
            
            # Create inline keyboard buttons for this address with alias names
            button_row = [
                InlineKeyboardButton(f"🔍 Check {label}", callback_data=f"check_{address}"),
                InlineKeyboardButton(f"🗑️ Remove {label}", callback_data=f"remove_{address}")
            ]
            keyboards.append(button_row)
        
        # Add summary
        message += f"📈 Total: {len(all_tracked_addresses)} addresses\n"
        message += f"📌 Dynamic: {len(self.notifier.dynamic_addresses)} addresses\n"
        message += f"⚙️ Static: 0 addresses\n\n"
        message += "💡 Use buttons below to check positions or remove addresses"
        
        # Create inline keyboard markup
        reply_markup = InlineKeyboardMarkup(keyboards)
        
        # Send message with buttons
        await update.message.reply_text(message, reply_markup=reply_markup)
        
        # Log the action
        username = update.message.from_user.username or "Unknown"
        user_id = update.message.from_user.id
        self.logger.info(f"Interactive /list used by @{username} (ID: {user_id}) - {len(all_tracked_addresses)} addresses shown")
    
    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remove command - available to everyone"""
        await self.notifier.handle_remove_command(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - available to everyone"""
        # Register user for broadcasts
        user = update.message.from_user
        self.notifier.add_user(user.id, user.username, user.first_name)
        
        help_text = (
            "🐋 Whale Tracker Commands\n\n"
            "🌍 All Commands (available to everyone):\n\n"
            "📌 /add address:label\n"
            "   Add new address with custom label\n"
            "   Example: /add 0x1234...5678:My Whale\n\n"
            "📌 /add address\n"
            "   Add new address with random unique alias\n"
            "   Example: /add 0x1234...5678 (generates alias like 'Swift Whale')\n\n"
            "🗑️ /remove address\n"
            "   Remove address from tracking\n"
            "   Example: /remove 0x1234...5678\n\n"
            "📊 /list\n"
            "   Show all tracked addresses with interactive buttons\n"
            "   Use 🔍 Check to see positions or 🗑️ Remove to stop tracking\n\n"
            "🔍 /check address\n"
            "   Check current positions for any address\n"
            "   Example: /check 0x1234...5678\n\n"
            "❓ /help\n"
            "   Show this help message\n\n"
            "📝 Notes:\n"
            "• Addresses must be 42 characters long\n"
            "• Addresses must start with 0x\n"
            "• Only actual position changes are alerted\n"
            "• Opening positions are skipped to avoid spam\n"
            "• Changes take effect in next polling cycle (10s)"
        )
        
        await update.message.reply_text(help_text)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - available to everyone"""
        # Register user for broadcasts
        user = update.message.from_user
        self.notifier.add_user(user.id, user.username, user.first_name)
        
        username = update.message.from_user.first_name or "User"
        
        welcome_text = (
            f"🐋 Welcome to Whale Tracker, {username}!\n\n"
            "This bot helps you monitor Hyperliquid trading positions.\n\n"
            "🌍 Available Commands:\n"
            "📌 /add address:label - Add addresses to track\n"
            "🔍 /check address - Check positions for any address\n"
            "📊 /list - Show tracked addresses with interactive buttons\n"
            "❓ /help - Show all commands\n\n"
            "💡 Try: /check 0x[address] to see someone's positions!\n"
            "💡 Or: /add 0x[address]:Label or /add 0x[address] (auto-alias)!\n\n"
            "📊 Built for tracking whale movements on Hyperliquid DEX\n\n"
            "🔔 You'll now receive whale movement alerts!"
        )
        
        # Log the new user
        user_id = update.message.from_user.id
        username_log = update.message.from_user.username or "no_username"
        self.logger.info(f"New user started bot: @{username_log} (ID: {user_id})")
        
        await update.message.reply_text(welcome_text)
    
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command - available to everyone"""
        # Register user for broadcasts
        user = update.message.from_user
        self.notifier.add_user(user.id, user.username, user.first_name)
        
        # No authorization check - this command is public
        
        # Get the address from command arguments
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: /check address\n\n"
                "📌 Example:\n"
                "/check 0x1234567890123456789012345678901234567890\n\n"
                "💡 Tip: Use the full 42-character address starting with 0x"
            )
            return
        
        address = context.args[0].strip()
        
        # Validate address format
        if not self._validate_address(address):
            await update.message.reply_text(
                "❌ Invalid Address Format\n\n"
                "📝 Address must be:\n"
                "• 42 characters long\n"
                "• Start with 0x\n"
                "• Contain only hexadecimal characters\n\n"
                "📌 Example:\n"
                "0x1234567890123456789012345678901234567890"
            )
            return
        
        # Show loading message
        loading_message = await update.message.reply_text("🔍 Checking positions for address...")
        
        try:
            # Get positions for the address
            positions = await self._get_address_positions(address)
            
            # Format and send response
            response = self._format_positions_response(address, positions)
            await loading_message.edit_text(response)
            
            # Log the check action with user info
            username = update.message.from_user.username or "Unknown"
            user_id = update.message.from_user.id
            self.logger.info(f"Public /check used by @{username} (ID: {user_id}) for address: {address[:10]}... ({len(positions)} positions)")
            
        except Exception as e:
            self.logger.error(f"Error checking positions for {address}: {e}")
            await loading_message.edit_text(
                f"❌ Error checking positions\n\n"
                f"Failed to fetch data for address:\n"
                f"{address[:10]}...{address[-8:]}\n\n"
                f"This could be due to:\n"
                f"• Network connectivity issues\n"
                f"• API rate limiting\n"
                f"• Invalid address (not on Hyperliquid)\n"
                f"• Temporary API issues"
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button press callbacks"""
        query = update.callback_query
        
        # Always answer the callback query to remove the loading spinner
        await query.answer()
        
        # Register user for broadcasts
        user = query.from_user
        self.notifier.add_user(user.id, user.username, user.first_name)
        
        # Parse the callback data
        callback_data = query.data
        
        if callback_data.startswith("check_"):
            await self._handle_check_button(query, callback_data)
        elif callback_data.startswith("remove_"):
            await self._handle_remove_button(query, callback_data)
        else:
            await query.edit_message_text("❌ Unknown button action")
    
    async def _handle_check_button(self, query, callback_data: str):
        """Handle check button press"""
        # Extract address from callback data
        address = callback_data.replace("check_", "")
        
        # Show loading message
        await query.edit_message_text("🔍 Checking positions for address...\n\n⏳ Please wait...")
        
        try:
            # Get positions for the address
            positions = await self._get_address_positions(address)
            
            # Format and send response
            response = self._format_positions_response(address, positions)
            await query.edit_message_text(response)
            
            # Log the action
            username = query.from_user.username or "Unknown"
            user_id = query.from_user.id
            self.logger.info(f"Check button used by @{username} (ID: {user_id}) for address: {address[:10]}... ({len(positions)} positions)")
            
        except Exception as e:
            self.logger.error(f"Error checking positions via button for {address}: {e}")
            await query.edit_message_text(
                f"❌ Error checking positions\n\n"
                f"Failed to fetch data for address:\n"
                f"{address[:10]}...{address[-8:]}\n\n"
                f"This could be due to:\n"
                f"• Network connectivity issues\n"
                f"• API rate limiting\n"
                f"• Invalid address (not on Hyperliquid)\n"
                f"• Temporary API issues\n\n"
                f"💡 Try /check {address} for a fresh attempt"
            )
    
    async def _handle_remove_button(self, query, callback_data: str):
        """Handle remove button press"""
        # Extract address from callback data
        address = callback_data.replace("remove_", "")
        
        # Check if address is being tracked
        if address not in self.notifier.dynamic_addresses:
            await query.edit_message_text(
                f"⚠️ Address not found\n\n"
                f"Address {address[:10]}...{address[-8:]} is not being tracked.\n\n"
                f"💡 Use /list to see current tracked addresses"
            )
            return
        
        # Get label before removal
        all_labels = self.notifier.get_all_address_labels()
        label = all_labels.get(address, f"{address[:6]}...{address[-4:]}")
        
        # Remove from dynamic addresses
        del self.notifier.dynamic_addresses[address]
        self.notifier._save_dynamic_addresses()
        
        # Send confirmation
        await query.edit_message_text(
            f"✅ Address Removed Successfully!\n\n"
            f"📍 {label}\n"
            f"📊 {address[:10]}...{address[-8:]}\n\n"
            f"🛑 No longer monitoring this address\n\n"
            f"💡 Use /list to see remaining tracked addresses"
        )
        
        # Send notification to all users about removal
        await self.notifier.send_address_removed_notification(address, label)
        
        # Log the action
        username = query.from_user.username or "Unknown"
        user_id = query.from_user.id
        self.logger.info(f"Remove button used by @{username} (ID: {user_id}): {address} ({label})")
    
    async def echo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Echo any text message - available to everyone"""
        # Register user for broadcasts
        user = update.message.from_user
        self.notifier.add_user(user.id, user.username, user.first_name)
        
        # Get the original message text
        original_text = update.message.text
        
        # Echo the message back with a small indicator
        echo_text = f"🔄 Echo: {original_text}"
        
        # Send the echo message back
        await update.message.reply_text(echo_text)
        
        # Log the echo action with user info
        username = update.message.from_user.username or "Unknown"
        user_id = update.message.from_user.id
        self.logger.info(f"Echo used by @{username} (ID: {user_id}): {original_text}")
    
    def _validate_address(self, address: str) -> bool:
        """Validate if an address looks like a valid Ethereum address"""
        if not address:
            return False
        
        # Basic Ethereum address validation
        if not address.startswith('0x'):
            return False
        
        if len(address) != 42:
            return False
        
        # Check if it's hexadecimal (after 0x prefix)
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    
    async def _get_address_positions(self, address: str) -> dict:
        """Get current positions for a specific address using Hyperliquid API"""
        from hyperliquid.info import Info
        from decimal import Decimal
        
        try:
            # Initialize info client
            info_client = Info(self.config.API_URL, skip_ws=True)
            
            # Get user state from Hyperliquid API
            user_state = info_client.user_state(address)
            
            positions = {}
            
            # Check if user has any positions
            if not user_state or 'assetPositions' not in user_state:
                return positions
            
            # Process each position
            for pos_data in user_state['assetPositions']:
                position = pos_data['position']
                
                # Skip if position size is zero
                if float(position['szi']) == 0:
                    continue
                
                symbol = position['coin']
                size = Decimal(position['szi'])
                entry_price = Decimal(position['entryPx']) if position['entryPx'] else Decimal('0')
                unrealized_pnl = Decimal(position['unrealizedPnl'])
                
                # Calculate market value
                market_value = abs(size) * entry_price
                
                # Determine position side
                side = "long" if size > 0 else "short"
                
                # Store position info
                positions[symbol] = {
                    'symbol': symbol,
                    'size': abs(size),
                    'side': side,
                    'entry_price': entry_price,
                    'market_value': market_value,
                    'unrealized_pnl': unrealized_pnl
                }
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Error getting positions for {address}: {e}")
            raise
    
    def _format_positions_response(self, address: str, positions: dict) -> str:
        """Format positions data for Telegram response"""
        # Get address label if it exists in tracked addresses
        labels = self.notifier.get_all_address_labels()
        address_label = labels.get(address, f"{address[:6]}...{address[-4:]}")
        
        # Build response message
        message = f"📊 Position Check Results\n\n"
        message += f"📍 {address_label}\n"
        message += f"🔗 View on Hyperdash: https://hyperdash.info/trader/{address}\n\n"
        
        if not positions:
            message += f"❌ No Open Positions\n\n"
            message += f"This address currently has no open positions on Hyperliquid.\n\n"
            message += f"💡 Note: This could mean:\n"
            message += f"• Address has no trading activity\n"
            message += f"• All positions have been closed\n"
            message += f"• Address is not active on Hyperliquid"
        else:
            # Calculate total portfolio value
            total_value = sum(pos['market_value'] for pos in positions.values())
            total_pnl = sum(pos['unrealized_pnl'] for pos in positions.values())
            
            message += f"✅ {len(positions)} Open Position(s)\n"
            message += f"💰 Total Value: ${total_value:,.2f}\n"
            message += f"📈 Total PnL: ${total_pnl:+,.2f}\n\n"
            
            # Sort positions by market value (largest first)
            sorted_positions = sorted(positions.values(), key=lambda x: x['market_value'], reverse=True)
            
            # Add each position
            for i, pos in enumerate(sorted_positions, 1):
                side_emoji = "🟢" if pos['side'] == 'long' else "🔴"
                
                message += f"{side_emoji} {pos['symbol']} {pos['side'].upper()}\n"
                message += f"📦 Size: {pos['size']:.4f}\n"
                message += f"💵 Entry: ${pos['entry_price']:,.2f}\n"
                message += f"💰 Value: ${pos['market_value']:,.2f}\n"
                message += f"📊 PnL: ${pos['unrealized_pnl']:+,.2f}\n"
                
                # Add separator if not the last position
                if i < len(sorted_positions):
                    message += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Add timestamp
        from datetime import datetime
        message += f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    async def start_command_handler(self):
        """Start the command handler"""
        try:
            if not self.config.TELEGRAM_BOT_TOKEN:
                self.logger.error("Telegram bot token not configured")
                return
            
            # Create application with timeout settings
            self.application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("add", self.add_command))
            self.application.add_handler(CommandHandler("remove", self.remove_command))
            self.application.add_handler(CommandHandler("list", self.list_command))
            self.application.add_handler(CommandHandler("check", self.check_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("start", self.start_command))
            
            # Add callback handler for button presses
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Add message handler for echo functionality
            # This handles all text messages that are not commands
            self.application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo_message))
            
            self.logger.info("🤖 Telegram command handler started")
            self.logger.info("🌍 All commands available to everyone: /add, /remove, /list, /check, /help, /start")
            self.logger.info("🔘 Interactive buttons enabled for /list command")
            self.logger.info("🔄 Echo functionality enabled for everyone")
            self.logger.info("💡 Use /help in Telegram for usage instructions")
            
            # Start the bot with better error handling
            try:
                await self.application.initialize()
                await self.application.start()
                
                # Test connection first
                self.logger.info("🔍 Testing bot connection...")
                bot_info = await self.application.bot.get_me()
                self.logger.info(f"✅ Connected as: @{bot_info.username}")
                
                # Start polling
                self.logger.info("🔄 Starting polling for commands...")
                await self.application.updater.start_polling(
                    drop_pending_updates=True,
                    timeout=30
                )
                
                self.logger.info("✅ Command handler is now listening for commands!")
                
                # Keep running
                while True:
                    await asyncio.sleep(1)
                    
            except Exception as startup_error:
                self.logger.error(f"Failed to start bot: {startup_error}")
                self.logger.error("This might be due to:")
                self.logger.error("• Invalid bot token")
                self.logger.error("• Network connectivity issues") 
                self.logger.error("• Firewall blocking Telegram API")
                raise
                
        except KeyboardInterrupt:
            self.logger.info("📴 Command handler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Error in command handler: {e}")
        finally:
            if self.application and self.application.updater.running:
                try:
                    self.logger.info("🛑 Stopping command handler...")
                    await self.application.updater.stop()
                    await self.application.stop()
                    await self.application.shutdown()
                    self.logger.info("✅ Command handler stopped cleanly")
                except Exception as cleanup_error:
                    self.logger.error(f"Error during cleanup: {cleanup_error}")


async def main():
    """Main function"""
    print("🤖 Starting Telegram Command Handler for Whale Tracker")
    print("=" * 60)
    print("📋 This handler enables these Telegram commands:")
    print("🌍 All commands (available to everyone):")
    print("   /add address:label - Add new address with custom label")
    print("   /add address - Add new address with random unique alias")
    print("   /remove address - Remove address from tracking")
    print("   /list - Show tracked addresses with interactive buttons")
    print("   /check address - Check positions for any address")
    print("   /help - Show help message")
    print("   /start - Show welcome message")
    print("🔄 Echo functionality (everyone):")
    print("   Any text message will be echoed back")
    print("=" * 60)
    print("💡 Run this alongside your main whale tracker")
    print("🔄 Starting command handler...")
    
    handler = WhaleTrackerCommandHandler()
    await handler.start_command_handler()


if __name__ == "__main__":
    asyncio.run(main()) 