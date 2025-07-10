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
        
        # File to store all user chat IDs for broadcasting
        self.user_chat_ids_file = f"{self.config.DATA_DIR}/user_chat_ids.json"
        
        # Load dynamically added addresses
        self.dynamic_addresses = self._load_dynamic_addresses()
        
        # Load user chat IDs for broadcasting
        self.user_chat_ids = self._load_user_chat_ids()
        
        # Add main chat ID as a user if configured and no users exist
        if self.config.TELEGRAM_CHAT_ID and not self.user_chat_ids:
            self.add_user(int(self.config.TELEGRAM_CHAT_ID), "MainChat", "Main User")
        
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
        """Send a message to all users (broadcast)"""
        if not self.enabled or not self.bot:
            return False
        
        # Get all user chat IDs for broadcasting
        all_chat_ids = self.get_all_user_chat_ids()
        
        # If no users registered, fall back to main chat ID (if configured)
        if not all_chat_ids and self.config.TELEGRAM_CHAT_ID:
            all_chat_ids = [int(self.config.TELEGRAM_CHAT_ID)]
        
        if not all_chat_ids:
            self.logger.warning("No users to send message to. Users need to interact with the bot first.")
            return False
        
        success_count = 0
        
        for chat_id in all_chat_ids:
            try:
                # Use plain text instead of HTML formatting
                parse_mode = None
                
                # Add timeout to message sending
                await asyncio.wait_for(
                    self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    ),
                    timeout=15.0  # 15 second timeout
                )
                success_count += 1
                
                # Small delay between messages to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                self.logger.error(f"Failed to send message to {chat_id}: Connection timed out")
            except (TimedOut, NetworkError) as e:
                self.logger.error(f"Failed to send message to {chat_id}: Network error - {e}")
            except Exception as e:
                self.logger.error(f"Failed to send message to {chat_id}: {e}")
        
        if success_count > 0:
            self.logger.info(f"Successfully sent message to {success_count}/{len(all_chat_ids)} users")
            return True
        else:
            self.logger.error("Failed to send message to any users")
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
            self.logger.debug("Position change notifications disabled in config")
            return True
        
        # Skip "opened" positions - only send alerts for actual changes
        if change.change_type == "opened":
            self.logger.debug(f"Skipping 'opened' position notification for {change.symbol}")
            return True
        
        self.logger.info(f"📨 Sending position change notification: {change.change_type} {change.symbol}")
        
        message = self._format_position_change_message(change)
        result = await self.send_message(message)
        
        if result:
            self.logger.info(f"✅ Position change notification sent successfully: {change.symbol}")
        else:
            self.logger.error(f"❌ Failed to send position change notification: {change.symbol}")
        
        return result
    
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
    
    def _load_user_chat_ids(self) -> Dict[str, int]:
        """Load all user chat IDs from file"""
        try:
            if os.path.exists(self.user_chat_ids_file):
                with open(self.user_chat_ids_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading user chat IDs: {e}")
        return {}
    
    def _save_user_chat_ids(self):
        """Save all user chat IDs to file"""
        try:
            os.makedirs(self.config.DATA_DIR, exist_ok=True)
            with open(self.user_chat_ids_file, 'w') as f:
                json.dump(self.user_chat_ids, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving user chat IDs: {e}")
    
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
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add a new user to the broadcast list"""
        user_key = str(user_id)
        user_info = {
            'chat_id': user_id,
            'username': username or 'Unknown',
            'first_name': first_name or 'Unknown',
            'added_at': datetime.now().isoformat()
        }
        
        if user_key not in self.user_chat_ids:
            self.user_chat_ids[user_key] = user_info
            self._save_user_chat_ids()
            self.logger.info(f"Added new user to broadcast list: @{username} (ID: {user_id})")
        else:
            # Update existing user info
            self.user_chat_ids[user_key].update({
                'username': username or self.user_chat_ids[user_key].get('username', 'Unknown'),
                'first_name': first_name or self.user_chat_ids[user_key].get('first_name', 'Unknown')
            })
            self._save_user_chat_ids()
    
    def get_all_user_chat_ids(self) -> List[int]:
        """Get all user chat IDs for broadcasting"""
        return [user_info['chat_id'] for user_info in self.user_chat_ids.values()]
    
    async def handle_add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command to add new addresses"""
        try:
            # Register user for broadcasts
            user = update.message.from_user
            self.add_user(user.id, user.username, user.first_name)
            
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
            
            # Check if already tracking (only check dynamic addresses)
            if address in self.dynamic_addresses:
                await update.message.reply_text(
                    f"⚠️ Address {address[:10]}... is already being tracked"
                )
                return
            
            # Add to dynamic addresses
            self.dynamic_addresses[address] = label
            self._save_dynamic_addresses()
            
            # Note: No longer adding to config.TRACKED_ADDRESSES - use only dynamic addresses
            
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
            
            # Log the action with user info
            username = update.message.from_user.username or "Unknown"
            user_id = update.message.from_user.id
            self.logger.info(f"Address added by @{username} (ID: {user_id}): {address} ({label})")
            
        except Exception as e:
            self.logger.error(f"Error handling add command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def handle_list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command to show tracked addresses"""
        try:
            # Register user for broadcasts
            user = update.message.from_user
            self.add_user(user.id, user.username, user.first_name)
            
            message = "📊 Tracked Addresses:\n\n"
            
            # Get all tracked addresses (only dynamic from Telegram)
            all_tracked_addresses = self.get_all_tracked_addresses()
            
            for i, address in enumerate(all_tracked_addresses, 1):
                label = self.dynamic_addresses.get(address, f"{address[:6]}...{address[-4:]}")
                
                message += f"📌 {label}\n"
                message += f"   📍 {address[:10]}...{address[-8:]}\n"
                message += f"   🔗 https://hyperdash.info/trader/{address}\n\n"
            
            message += f"📈 Total: {len(all_tracked_addresses)} addresses\n"
            message += f"📌 Dynamic: {len(self.dynamic_addresses)} addresses\n"
            message += f"⚙️ Static: 0 addresses"
            
            await update.message.reply_text(message)
            
            # Log the action with user info
            username = update.message.from_user.username or "Unknown"
            user_id = update.message.from_user.id
            self.logger.info(f"List command used by @{username} (ID: {user_id}) - {len(all_tracked_addresses)} addresses shown")
            
        except Exception as e:
            self.logger.error(f"Error handling list command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def handle_remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remove command to remove addresses"""
        try:
            # Register user for broadcasts
            user = update.message.from_user
            self.add_user(user.id, user.username, user.first_name)
            
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
            
            # Check if address is being tracked (only check dynamic addresses)
            if address not in self.dynamic_addresses:
                await update.message.reply_text(
                    f"⚠️ Address {address[:10]}... is not being tracked"
                )
                return
            
            # Get label before removal
            all_labels = self.get_all_address_labels()
            label = all_labels.get(address, f"{address[:6]}...{address[-4:]}")
            
            # Remove from dynamic addresses
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
            
            # Log the action with user info
            username = update.message.from_user.username or "Unknown"
            user_id = update.message.from_user.id
            self.logger.info(f"Address removed by @{username} (ID: {user_id}): {address} ({label})")
            
        except Exception as e:
            self.logger.error(f"Error handling remove command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    def get_all_tracked_addresses(self) -> List[str]:
        """Get all tracked addresses (only dynamic from Telegram)"""
        # Only return dynamic addresses added via Telegram - ignore config file addresses
        return list(self.dynamic_addresses.keys())
    
    def get_all_address_labels(self) -> Dict[str, str]:
        """Get all address labels (only dynamic from Telegram)"""
        return self.dynamic_addresses.copy()


# Global notifier instance
_notifier_instance = None

def get_telegram_notifier() -> TelegramNotifier:
    """Get the global Telegram notifier instance"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier()
    return _notifier_instance 