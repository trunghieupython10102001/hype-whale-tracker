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
    from telegram.error import TelegramError, TimedOut, NetworkError
    from telegram.constants import ParseMode
    from telegram.request import HTTPXRequest
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
    TimedOut = Exception
    NetworkError = Exception
    HTTPXRequest = None

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
            
            # Create custom request object with better timeout settings
            if HTTPXRequest:
                request = HTTPXRequest(
                    connection_pool_size=8,
                    connect_timeout=30.0,
                    read_timeout=30.0,
                    write_timeout=30.0,
                    pool_timeout=5.0
                )
                # Create bot with custom request settings for better reliability
                self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN, request=request)
            else:
                # Fallback for older versions
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
            # Try to get bot info first (lighter than sending message)
            self.logger.info("Testing Telegram bot connection...")
            
            # Set a reasonable timeout for connection test
            bot_info = await asyncio.wait_for(
                self.bot.get_me(),
                timeout=15.0  # 15 second timeout
            )
            
            self.logger.info(f"✅ Connected to Telegram as @{bot_info.username}")
            
            # Try to send a simple test message
            test_message = "🤖 Whale Tracker Test\n\nConnection successful! ✅"
            
            success = await asyncio.wait_for(
                self.send_message(test_message),
                timeout=10.0  # 10 second timeout for message
            )
            
            if success:
                self.logger.info("Telegram bot test message sent successfully")
                return True
            else:
                return False
            
        except asyncio.TimeoutError:
            self.logger.error("Telegram connection timed out - check network connectivity or firewall")
            self.logger.error("💡 Tip: Telegram may be blocked on your network")
            return False
        except (TimedOut, NetworkError) as e:
            self.logger.error(f"Telegram network error: {e}")
            self.logger.error("💡 This usually indicates network connectivity issues")
            return False
        except Exception as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg or 'timed out' in error_msg:
                self.logger.error("Telegram connection timed out - check network connectivity")
                self.logger.error("💡 Tip: Try running on a server where Telegram is not blocked")
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
            # Use plain text instead of HTML formatting
            parse_mode = None
            
            # Add timeout to message sending
            await asyncio.wait_for(
                self.bot.send_message(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                ),
                timeout=15.0  # 15 second timeout
            )
            return True
            
        except asyncio.TimeoutError:
            self.logger.error("Failed to send Telegram message: Connection timed out")
            return False
        except (TimedOut, NetworkError) as e:
            self.logger.error(f"Failed to send Telegram message: Network error - {e}")
            return False
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
        message = f"{emoji} {address_label}\n"
        message += f"{action} {change.symbol} {side}\n"
        message += f"{details}\n"
        message += f"🕐 {change.timestamp.strftime('%H:%M:%S')}\n"
        message += f"📊 View on Hyperdash: https://hyperdash.info/trader/{change.address}"
        
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
        
        message = f"📊 Daily Whale Activity Summary\n"
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
            message += f"🔥 Top Activities:\n"
            for activity in summary_data['top_activities'][:5]:  # Top 5
                message += f"• {activity}\n"
        
        return await self.send_message(message)
    
    async def send_error_alert(self, error_message: str) -> bool:
        """Send an error alert"""
        message = f"⚠️ Whale Tracker Error\n\n"
        message += f"❌ {error_message}\n"
        message += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n\n"
        message += "Please check the logs for more details."
        
        return await self.send_message(message)
    
    async def send_startup_message(self) -> bool:
        """Send a startup notification"""
        message = f"🚀 Whale Tracker Started\n\n"
        message += f"📡 Monitoring {len(self.config.TRACKED_ADDRESSES)} addresses\n"
        message += f"⏱️ Polling every {self.config.POLLING_INTERVAL} seconds\n"
        message += f"💰 Min position: ${self.config.MIN_POSITION_SIZE:,}\n"
        message += f"📊 Min change: ${self.config.MIN_CHANGE_THRESHOLD:,}\n\n"
        message += f"🔍 Watching for whale movements..."
        
        return await self.send_message(message)
    
    async def send_shutdown_message(self) -> bool:
        """Send a shutdown notification"""
        message = f"🛑 Whale Tracker Stopped\n\n"
        message += f"📊 Monitoring session ended\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    async def send_address_added_notification(self, address: str, label: str) -> bool:
        """Send notification when a new address is added via Telegram"""
        message = f"🆕 New Address Added to Tracking\n\n"
        message += f"📍 {label}\n"
        message += f"📊 {address[:10]}...{address[-8:]}\n"
        message += f"🔗 View on Hyperdash: https://hyperdash.info/trader/{address}\n\n"
        message += f"⚡ Now monitoring for position changes\n"
        message += f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        
        return await self.send_message(message)
    
    async def send_address_removed_notification(self, address: str, label: str) -> bool:
        """Send notification when an address is removed"""
        message = f"🗑️ Address Removed from Tracking\n\n"
        message += f"📍 {label}\n"
        message += f"📊 {address[:10]}...{address[-8:]}\n\n"
        message += f"🛑 No longer monitoring this address\n"
        message += f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        
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
            
            # Add to runtime tracking
            self.config.TRACKED_ADDRESSES.append(address)
            
            # Send confirmation reply
            await update.message.reply_text(
                f"✅ Address Added Successfully!\n\n"
                f"📍 {label}\n"
                f"📊 {address[:10]}...{address[-8:]}\n"
                f"🔗 View on Hyperdash: https://hyperdash.info/trader/{address}\n\n"
                f"⚡ Tracker will start monitoring this address in the next polling cycle (10 seconds)\n"
                f"🔔 You'll receive alerts for position changes (increases, decreases, closures)"
            )
            
            # Send notification to main chat about new address
            await self.send_address_added_notification(address, label)
            
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
            
            message = "📊 Tracked Addresses:\n\n"
            
            # Get all labels (static + dynamic)
            all_labels = self.config.get_address_labels()
            all_labels.update(self.dynamic_addresses)
            
            # Get all unique addresses being tracked
            all_tracked_addresses = self.get_all_tracked_addresses()
            
            # Count static addresses (those NOT in dynamic_addresses)
            static_count = 0
            for address in all_tracked_addresses:
                if address not in self.dynamic_addresses:
                    static_count += 1
            
            for i, address in enumerate(all_tracked_addresses, 1):
                label = all_labels.get(address, f"{address[:6]}...{address[-4:]}")
                source = "📌" if address in self.dynamic_addresses else "⚙️"
                
                message += f"{source} {label}\n"
                message += f"   📍 {address[:10]}...{address[-8:]}\n"
                message += f"   🔗 https://hyperdash.info/trader/{address}\n\n"
            
            message += f"📈 Total: {len(all_tracked_addresses)} addresses\n"
            message += f"📌 Dynamic: {len(self.dynamic_addresses)} addresses\n"
            message += f"⚙️ Static: {static_count} addresses"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            self.logger.error(f"Error handling list command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def handle_remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remove command to remove addresses"""
        try:
            # Check if user is authorized
            if str(update.message.chat_id) != self.config.TELEGRAM_CHAT_ID:
                await update.message.reply_text("❌ Unauthorized access")
                return
            
            if not context.args:
                await update.message.reply_text(
                    "📋 Usage: /remove address\n"
                    "Example: /remove 0x1234...5678\n"
                    "Use /list to see tracked addresses"
                )
                return
            
            address = " ".join(context.args).strip()
            
            # Validate address format
            if not self._validate_address(address):
                await update.message.reply_text(
                    "❌ Invalid address format\n"
                    "Address must be 42 characters long and start with 0x"
                )
                return
            
            # Check if address is being tracked
            if address not in self.config.TRACKED_ADDRESSES:
                await update.message.reply_text(
                    f"⚠️ Address {address[:10]}... is not being tracked"
                )
                return
            
            # Get label before removal
            all_labels = self.get_all_address_labels()
            label = all_labels.get(address, f"{address[:6]}...{address[-4:]}")
            
            # Remove from tracking
            if address in self.config.TRACKED_ADDRESSES:
                self.config.TRACKED_ADDRESSES.remove(address)
            
            # Remove from dynamic addresses if it exists there
            if address in self.dynamic_addresses:
                del self.dynamic_addresses[address]
                self._save_dynamic_addresses()
            
            # Send confirmation
            await update.message.reply_text(
                f"✅ Address Removed Successfully!\n\n"
                f"📍 {label}\n"
                f"📊 {address[:10]}...{address[-8:]}\n\n"
                f"🛑 No longer monitoring this address"
            )
            
            # Send notification to main chat
            await self.send_address_removed_notification(address, label)
            
            self.logger.info(f"Removed address via Telegram: {address} ({label})")
            
        except Exception as e:
            self.logger.error(f"Error handling remove command: {e}")
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