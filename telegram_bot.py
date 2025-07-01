"""
Telegram Bot module for sending whale tracking notifications
"""

import asyncio
import logging
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.error import TelegramError
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
    Update = None
    Application = None
    CommandHandler = None
    MessageHandler = None
    filters = None
    ContextTypes = None
    ParseMode = None
    TelegramError = Exception

from config import Config


class TelegramNotifier:
    """Handles sending notifications via Telegram bot"""
    
    def __init__(self):
        self.config = Config
        self.logger = logging.getLogger('TelegramNotifier')
        self.bot: Optional[Bot] = None
        self.enabled = False
        self.application = None
        self.command_handler = None
        
        # File to store dynamically added addresses
        self.dynamic_addresses_file = f"{self.config.DATA_DIR}/dynamic_addresses.json"
        
        # Load dynamically added addresses
        self.dynamic_addresses = self._load_dynamic_addresses()
        
        # Initialize if Telegram is enabled and available
        if self.config.ENABLE_TELEGRAM_ALERTS and TELEGRAM_AVAILABLE:
            self._initialize_bot()
    
    def _initialize_bot(self):
        """Initialize the Telegram bot with command handlers"""
        try:
            if not self.config.TELEGRAM_BOT_TOKEN:
                self.logger.error("Telegram bot token not configured")
                return
            
            if not TELEGRAM_AVAILABLE:
                self.logger.error("python-telegram-bot library not available")
                return
            
            # Create bot with custom settings for better reliability
            self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            
            # Set up command handlers (optional - for advanced usage)
            # Note: Command handling requires running the bot application separately
            # For now, we'll just enable basic messaging functionality
            
            self.enabled = True
            self.logger.info("Telegram bot initialized successfully")
            self.logger.info("📋 Available commands: /add address:label, /list")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram bot: {e}")
            self.enabled = False
    
    async def test_connection(self) -> bool:
        """Test the Telegram bot connection"""
        if not self.enabled or not self.bot:
            return False
        
        try:
            # Try to send a simple test message first
            test_message = "🤖 Whale Tracker Test\n\nConnection successful! ✅"
            
            success = await self.send_message(test_message)
            if success:
                self.logger.info("Telegram bot test message sent successfully")
                return True
            else:
                return False
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg or 'timed out' in error_msg:
                self.logger.error("Telegram connection timed out - check network connectivity")
            elif 'unauthorized' in error_msg:
                self.logger.error("Telegram bot unauthorized - check bot token")
            elif 'forbidden' in error_msg:
                self.logger.error("Telegram bot forbidden - check chat ID or start chat with bot")
            else:
                self.logger.error(f"Telegram connection test failed: {e}")
            return False
    
    async def send_message(self, message: str, parse_mode: str = None) -> bool:
        """Send a message to the configured chat"""
        if not self.enabled or not self.bot:
            return False
        
        try:
            if parse_mode is None:
                parse_mode = ParseMode.HTML if TELEGRAM_AVAILABLE else None
                
            await self.bot.send_message(
                chat_id=self.config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def _format_position_change_message(self, change: Any) -> str:
        """Format a position change for Telegram with Hyperdash link"""
        # Get address label (including dynamic addresses)
        labels = self.get_all_address_labels()
        address_label = labels.get(change.address, f"{change.address[:6]}...{change.address[-4:]}")
        
        # Format based on change type
        if change.change_type == "opened":
            emoji = "🟢"
            action = "OPENED"
            details = f"${change.change_amount:,.2f} @ ${change.new_position.entry_price}"
            side = change.new_position.side.upper()
        
        elif change.change_type == "closed":
            emoji = "🔴"
            action = "CLOSED"
            details = f"${change.change_amount:,.2f}"
            side = change.old_position.side.upper()
            pnl = change.old_position.unrealized_pnl
            details += f"\nPnL: ${pnl:+,.2f}"
        
        elif change.change_type == "increased":
            emoji = "📈"
            action = "INCREASED"
            details = f"+${change.change_amount:,.2f}\nTotal: ${change.new_position.market_value:,.2f}"
            side = change.new_position.side.upper()
        
        elif change.change_type == "decreased":
            emoji = "📉"
            action = "DECREASED"
            details = f"-${change.change_amount:,.2f}\nTotal: ${change.new_position.market_value:,.2f}"
            side = change.new_position.side.upper()
        
        else:
            emoji = "ℹ️"
            action = change.change_type.upper()
            details = f"${change.change_amount:,.2f}"
            side = ""
        
        # Build message with Hyperdash link
        message = f"{emoji} <b>{address_label}</b>\n"
        message += f"{action} {change.symbol} {side}\n"
        message += f"{details}\n"
        message += f"🕐 {change.timestamp.strftime('%H:%M:%S')}\n"
        message += f"📊 <a href='https://hyperdash.xyz/address/{change.address}'>View on Hyperdash</a>"
        
        return message
    
    async def send_position_change(self, change: Any) -> bool:
        """Send a position change notification (skip opened positions)"""
        if not self.config.TELEGRAM_SEND_POSITION_CHANGES:
            return True
        
        # Skip "opened" positions - only send alerts for actual changes
        if change.change_type == "opened":
            self.logger.debug(f"Skipping 'opened' position notification for {change.symbol}")
            return True
        
        message = self._format_position_change_message(change)
        return await self.send_message(message)
    
    async def send_multiple_changes(self, changes: List[Any]) -> bool:
        """DEPRECATED: Send multiple position changes in a single message
        
        This method is kept for backward compatibility but is no longer used.
        The tracker now sends individual alerts for each position change.
        """
        # This method is deprecated - we now send individual alerts
        self.logger.warning("send_multiple_changes is deprecated - use individual alerts instead")
        
        # For backward compatibility, send individual changes
        for change in changes:
            await self.send_position_change(change)
        
        return True
    
    async def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send a daily summary of whale activity"""
        if not self.config.TELEGRAM_SEND_SUMMARY:
            return True
        
        message = f"📊 <b>Daily Whale Activity Summary</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Add summary statistics
        total_changes = summary_data.get('total_changes', 0)
        total_volume = summary_data.get('total_volume', 0)
        active_addresses = summary_data.get('active_addresses', 0)
        
        message += f"📈 Total Changes: {total_changes}\n"
        message += f"💰 Total Volume: ${total_volume:,.2f}\n"
        message += f"📍 Active Addresses: {active_addresses}\n\n"
        
        # Add top activities if available
        if 'top_activities' in summary_data:
            message += f"🔥 <b>Top Activities:</b>\n"
            for activity in summary_data['top_activities'][:5]:  # Top 5
                message += f"• {activity}\n"
        
        return await self.send_message(message)
    
    async def send_error_alert(self, error_message: str) -> bool:
        """Send an error alert"""
        message = f"⚠️ <b>Whale Tracker Error</b>\n\n"
        message += f"❌ {error_message}\n"
        message += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n\n"
        message += "Please check the logs for more details."
        
        return await self.send_message(message)
    
    async def send_startup_message(self) -> bool:
        """Send a startup notification"""
        message = f"🚀 <b>Whale Tracker Started</b>\n\n"
        message += f"📡 Monitoring {len(self.config.TRACKED_ADDRESSES)} addresses\n"
        message += f"⏱️ Polling every {self.config.POLLING_INTERVAL} seconds\n"
        message += f"💰 Min position: ${self.config.MIN_POSITION_SIZE:,}\n"
        message += f"📊 Min change: ${self.config.MIN_CHANGE_THRESHOLD:,}\n\n"
        message += f"🔍 Watching for whale movements..."
        
        return await self.send_message(message)
    
    async def send_shutdown_message(self) -> bool:
        """Send a shutdown notification"""
        message = f"🛑 <b>Whale Tracker Stopped</b>\n\n"
        message += f"📊 Monitoring session ended\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    def _load_dynamic_addresses(self) -> Dict[str, str]:
        """Load dynamically added addresses from file"""
        try:
            if os.path.exists(self.dynamic_addresses_file):
                with open(self.dynamic_addresses_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading dynamic addresses: {e}")
        return {}
    
    def _save_dynamic_addresses(self):
        """Save dynamically added addresses to file"""
        try:
            os.makedirs(self.config.DATA_DIR, exist_ok=True)
            with open(self.dynamic_addresses_file, 'w') as f:
                json.dump(self.dynamic_addresses, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving dynamic addresses: {e}")
    
    def _validate_address(self, address: str) -> bool:
        """Validate if an address looks like a valid Ethereum address"""
        if not address:
            return False
        
        # Basic Ethereum address validation
        if not address.startswith('0x'):
            return False
        
        if len(address) != 42:
            return False
        
        # Check if it's hexadecimal
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    
    async def handle_add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command to add new addresses"""
        try:
            # Check if user is authorized (from correct chat)
            if str(update.message.chat_id) != self.config.TELEGRAM_CHAT_ID:
                await update.message.reply_text("❌ Unauthorized access")
                return
            
            if not context.args:
                await update.message.reply_text(
                    "📋 Usage: /add address:label or /add address\n"
                    "Example: /add 0x1234...5678:My Whale\n"
                    "Example: /add 0x1234...5678"
                )
                return
            
            # Parse the command
            arg = " ".join(context.args)
            
            if ":" in arg:
                address, label = arg.split(":", 1)
                address = address.strip()
                label = label.strip()
            else:
                address = arg.strip()
                label = f"{address[:6]}...{address[-4:]}"
            
            # Validate address
            if not self._validate_address(address):
                await update.message.reply_text(
                    "❌ Invalid address format\n"
                    "Address must be 42 characters long and start with 0x"
                )
                return
            
            # Check if already tracking
            if address in self.config.TRACKED_ADDRESSES or address in self.dynamic_addresses:
                await update.message.reply_text(
                    f"⚠️ Address {address[:10]}... is already being tracked"
                )
                return
            
            # Add to dynamic addresses
            self.dynamic_addresses[address] = label
            self._save_dynamic_addresses()
            
            # Add to runtime tracking (we'll need to modify the tracker to check this)
            self.config.TRACKED_ADDRESSES.append(address)
            
            await update.message.reply_text(
                f"✅ Added new address to tracking:\n"
                f"📍 {label}\n"
                f"📊 {address[:10]}...{address[-8:]}\n"
                f"🔗 <a href='https://hyperdash.xyz/address/{address}'>View on Hyperdash</a>"
            )
            
            self.logger.info(f"Added new address via Telegram: {address} ({label})")
            
        except Exception as e:
            self.logger.error(f"Error handling add command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def handle_list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command to show tracked addresses"""
        try:
            # Check if user is authorized
            if str(update.message.chat_id) != self.config.TELEGRAM_CHAT_ID:
                await update.message.reply_text("❌ Unauthorized access")
                return
            
            message = "📊 <b>Tracked Addresses:</b>\n\n"
            
            # Get all labels (static + dynamic)
            all_labels = self.config.get_address_labels()
            all_labels.update(self.dynamic_addresses)
            
            total_addresses = len(self.config.TRACKED_ADDRESSES)
            
            for i, address in enumerate(self.config.TRACKED_ADDRESSES, 1):
                label = all_labels.get(address, f"{address[:6]}...{address[-4:]}")
                source = "📌" if address in self.dynamic_addresses else "⚙️"
                
                message += f"{source} <b>{label}</b>\n"
                message += f"   📍 {address[:10]}...{address[-8:]}\n"
                message += f"   🔗 <a href='https://hyperdash.xyz/address/{address}'>Hyperdash</a>\n\n"
            
            message += f"📈 Total: {total_addresses} addresses\n"
            message += f"📌 Dynamic: {len(self.dynamic_addresses)} addresses\n"
            message += f"⚙️ Static: {total_addresses - len(self.dynamic_addresses)} addresses"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            self.logger.error(f"Error handling list command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    def get_all_tracked_addresses(self) -> List[str]:
        """Get all tracked addresses (static + dynamic)"""
        return list(set(self.config.TRACKED_ADDRESSES))
    
    def get_all_address_labels(self) -> Dict[str, str]:
        """Get all address labels (static + dynamic)"""
        labels = self.config.get_address_labels().copy()
        labels.update(self.dynamic_addresses)
        return labels


# Global notifier instance
_notifier_instance = None

def get_telegram_notifier() -> TelegramNotifier:
    """Get the global Telegram notifier instance"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier()
    return _notifier_instance 