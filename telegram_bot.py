"""
Telegram Bot module for sending whale tracking notifications
"""

import asyncio
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

try:
    from telegram import Bot
    from telegram.error import TelegramError
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
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
        
        # Initialize if Telegram is enabled and available
        if self.config.ENABLE_TELEGRAM_ALERTS and TELEGRAM_AVAILABLE:
            self._initialize_bot()
    
    def _initialize_bot(self):
        """Initialize the Telegram bot"""
        try:
            if not self.config.TELEGRAM_BOT_TOKEN:
                self.logger.error("Telegram bot token not configured")
                return
            
            if not TELEGRAM_AVAILABLE:
                self.logger.error("python-telegram-bot library not available")
                return
            
            # Create bot with custom settings for better reliability
            self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            self.enabled = True
            self.logger.info("Telegram bot initialized successfully")
            
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
        # Get address label
        labels = self.config.get_address_labels()
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
        """Send a position change notification"""
        if not self.config.TELEGRAM_SEND_POSITION_CHANGES:
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


# Global notifier instance
_notifier_instance = None

def get_telegram_notifier() -> TelegramNotifier:
    """Get the global Telegram notifier instance"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier()
    return _notifier_instance 