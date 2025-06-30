"""
Position Tracker for Hyperliquid Whale Monitoring
This module handles tracking position changes for multiple addresses
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from decimal import Decimal

from hyperliquid.info import Info
from hyperliquid.utils import constants

from config import Config
from telegram_bot import get_telegram_notifier


@dataclass
class Position:
    """Data class to represent a position"""
    symbol: str
    size: Decimal
    side: str  # "long" or "short"
    entry_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'size': str(self.size),
            'side': self.side,
            'entry_price': str(self.entry_price),
            'market_value': str(self.market_value),
            'unrealized_pnl': str(self.unrealized_pnl),
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """Create position from dictionary"""
        return cls(
            symbol=data['symbol'],
            size=Decimal(data['size']),
            side=data['side'],
            entry_price=Decimal(data['entry_price']),
            market_value=Decimal(data['market_value']),
            unrealized_pnl=Decimal(data['unrealized_pnl']),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class PositionChange:
    """Data class to represent a position change event"""
    address: str
    symbol: str
    change_type: str  # "opened", "closed", "increased", "decreased"
    old_position: Optional[Position]
    new_position: Optional[Position]
    change_amount: Decimal
    timestamp: datetime


class HyperliquidTracker:
    """Main tracker class for monitoring Hyperliquid positions"""
    
    def __init__(self, test_mode: bool = False):
        self.config = Config
        self.logger = self._setup_logging()
        self.info_client = None
        self.test_mode = test_mode  # Enable test mode for offline testing
        self.test_cycle = 0  # Track test cycles for simulation
        
        # Initialize Telegram notifier
        self.telegram_notifier = get_telegram_notifier()
        
        # Storage for current positions
        # Format: {address: {symbol: Position}}
        self.current_positions: Dict[str, Dict[str, Position]] = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(self.config.DATA_DIR, exist_ok=True)
        
        # Load existing positions from file
        self._load_positions()
        
        if self.test_mode:
            self.logger.info("🧪 Test mode enabled - will simulate position changes")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration"""
        logger = logging.getLogger('HyperliquidTracker')
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if self.config.ENABLE_CONSOLE_OUTPUT:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if self.config.ENABLE_FILE_LOGGING:
            file_handler = logging.FileHandler(self.config.LOG_FILE)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_positions(self):
        """Load existing positions from file"""
        if os.path.exists(self.config.POSITIONS_FILE):
            try:
                with open(self.config.POSITIONS_FILE, 'r') as f:  
                    data = json.load(f)
                    
                # Convert back to Position objects
                for address, positions in data.items():
                    self.current_positions[address] = {}
                    for symbol, pos_data in positions.items():
                        self.current_positions[address][symbol] = Position.from_dict(pos_data)
                        
                self.logger.info(f"Loaded existing positions for {len(self.current_positions)} addresses")
            except Exception as e:
                self.logger.error(f"Error loading positions: {e}")
                self.current_positions = {}
    
    def _save_positions(self):
        """Save current positions to file"""
        try:
            # Convert Position objects to dictionaries for JSON serialization
            data = {}
            for address, positions in self.current_positions.items():
                data[address] = {}
                for symbol, position in positions.items():
                    data[address][symbol] = position.to_dict()
            
            with open(self.config.POSITIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving positions: {e}")
    
    async def initialize(self):
        """Initialize the Hyperliquid connection"""
        if self.test_mode:
            self.logger.info("🧪 Test mode - skipping API initialization")
            return
            
        try:
            # Initialize the info client
            self.info_client = Info(self.config.API_URL, skip_ws=True)
            self.logger.info(f"Connected to Hyperliquid API: {self.config.API_URL}")
            
            # Test connection with a simple call
            await self._test_connection()
            
            # Test Telegram connection if enabled
            if self.config.ENABLE_TELEGRAM_ALERTS:
                try:
                    telegram_ok = await self.telegram_notifier.test_connection()
                    if telegram_ok:
                        self.logger.info("Telegram bot connection successful")
                    else:
                        self.logger.warning("Telegram bot connection failed - continuing without notifications")
                        self.logger.warning("Check network connectivity or run 'python3 utils.py test-telegram' for diagnostics")
                except Exception as e:
                    self.logger.warning(f"Telegram initialization failed: {e}")
                    self.logger.warning("Continuing without Telegram notifications")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Hyperliquid connection: {e}")
            raise
    
    async def _test_connection(self):
        """Test the API connection"""
        try:
            # Try to get general info to test connection
            meta = self.info_client.meta()
            self.logger.info("API connection test successful")
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            raise
    
    async def get_user_positions(self, address: str) -> Dict[str, Position]:
        """Get current positions for a specific address"""
        
        # Test mode - return simulated positions
        if self.test_mode:
            return self._get_test_positions(address)
            
        try:
            # Get user state from Hyperliquid API
            user_state = self.info_client.user_state(address)
            
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
                
                # Skip positions below minimum size threshold
                if market_value < self.config.MIN_POSITION_SIZE:
                    continue
                
                # Determine position side
                side = "long" if size > 0 else "short"
                
                # Create Position object
                position_obj = Position(
                    symbol=symbol,
                    size=abs(size),
                    side=side,
                    entry_price=entry_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    timestamp=datetime.now()
                )
                
                positions[symbol] = position_obj
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Error getting positions for {address}: {e}")
            return {}
    
    def _get_test_positions(self, address: str) -> Dict[str, Position]:
        """Generate test positions for simulation"""
        positions = {}
        
        # Simulate different scenarios based on test cycle
        if self.test_cycle == 0:
            # Initial positions
            positions["ETH"] = Position(
                symbol="ETH",
                size=Decimal("10"),
                side="long",
                entry_price=Decimal("2500"),
                market_value=Decimal("25000"),
                unrealized_pnl=Decimal("500"),
                timestamp=datetime.now()
            )
            
        elif self.test_cycle == 1:
            # Add a new position (BTC opened)
            positions["ETH"] = Position(
                symbol="ETH",
                size=Decimal("12"),  # Increased size
                side="long",
                entry_price=Decimal("2500"),
                market_value=Decimal("30000"),
                unrealized_pnl=Decimal("750"),
                timestamp=datetime.now()
            )
            positions["BTC"] = Position(
                symbol="BTC",
                size=Decimal("0.5"),
                side="long",
                entry_price=Decimal("45000"),
                market_value=Decimal("22500"),
                unrealized_pnl=Decimal("1000"),
                timestamp=datetime.now()
            )
            
        elif self.test_cycle == 2:
            # Close ETH position, keep BTC, add SOL short
            positions["BTC"] = Position(
                symbol="BTC",
                size=Decimal("0.3"),  # Decreased size
                side="long",
                entry_price=Decimal("45000"),
                market_value=Decimal("13500"),
                unrealized_pnl=Decimal("500"),
                timestamp=datetime.now()
            )
            positions["SOL"] = Position(
                symbol="SOL",
                size=Decimal("1000"),
                side="short",
                entry_price=Decimal("100"),
                market_value=Decimal("100000"),
                unrealized_pnl=Decimal("-2000"),
                timestamp=datetime.now()
            )
            
        elif self.test_cycle >= 3:
            # Close all positions
            pass
        
        return positions
    
    def _detect_changes(self, address: str, old_positions: Dict[str, Position], 
                       new_positions: Dict[str, Position]) -> List[PositionChange]:
        """Detect changes between old and new positions"""
        changes = []
        
        # Get all symbols from both old and new positions
        all_symbols = set(old_positions.keys()) | set(new_positions.keys())
        
        for symbol in all_symbols:
            old_pos = old_positions.get(symbol)
            new_pos = new_positions.get(symbol)
            
            # Position opened
            if old_pos is None and new_pos is not None:
                change = PositionChange(
                    address=address,
                    symbol=symbol,
                    change_type="opened",
                    old_position=None,
                    new_position=new_pos,
                    change_amount=new_pos.market_value,
                    timestamp=datetime.now()
                )
                changes.append(change)
            
            # Position closed
            elif old_pos is not None and new_pos is None:
                change = PositionChange(
                    address=address,
                    symbol=symbol,
                    change_type="closed",
                    old_position=old_pos,
                    new_position=None,
                    change_amount=old_pos.market_value,
                    timestamp=datetime.now()
                )
                changes.append(change)
            
            # Position changed
            elif old_pos is not None and new_pos is not None:
                # Check if size changed significantly
                size_change = new_pos.market_value - old_pos.market_value
                
                if abs(size_change) >= self.config.MIN_CHANGE_THRESHOLD:
                    change_type = "increased" if size_change > 0 else "decreased"
                    
                    change = PositionChange(
                        address=address,
                        symbol=symbol,
                        change_type=change_type,
                        old_position=old_pos,
                        new_position=new_pos,
                        change_amount=abs(size_change),
                        timestamp=datetime.now()
                    )
                    changes.append(change)
        
        return changes
    
    def _format_position_change(self, change: PositionChange) -> str:
        """Format position change for display"""
        # Get address label or use shortened address
        labels = self.config.get_address_labels()
        address_label = labels.get(change.address, f"{change.address[:6]}...{change.address[-4:]}")
        
        if change.change_type == "opened":
            return (f"🟢 {address_label} OPENED {change.symbol} {change.new_position.side.upper()} "
                   f"${change.change_amount:,.2f} @ ${change.new_position.entry_price}")
        
        elif change.change_type == "closed":
            return (f"🔴 {address_label} CLOSED {change.symbol} {change.old_position.side.upper()} "
                   f"${change.change_amount:,.2f} "
                   f"PnL: ${change.old_position.unrealized_pnl:+,.2f}")
        
        elif change.change_type == "increased":
            return (f"📈 {address_label} INCREASED {change.symbol} {change.new_position.side.upper()} "
                   f"+${change.change_amount:,.2f} "
                   f"Total: ${change.new_position.market_value:,.2f}")
        
        elif change.change_type == "decreased":
            return (f"📉 {address_label} DECREASED {change.symbol} {change.new_position.side.upper()} "
                   f"-${change.change_amount:,.2f} "
                   f"Total: ${change.new_position.market_value:,.2f}")
        
        return f"Position change: {change.change_type}"
    
    async def check_all_addresses(self):
        """Check all tracked addresses for position changes"""
        all_changes = []
        
        for address in self.config.TRACKED_ADDRESSES:
            try:
                # Get current positions
                new_positions = await self.get_user_positions(address)
                
                # Get old positions
                old_positions = self.current_positions.get(address, {})
                
                # Detect changes
                changes = self._detect_changes(address, old_positions, new_positions)
                
                # Update stored positions
                self.current_positions[address] = new_positions
                
                # Add to all changes
                all_changes.extend(changes)
                
            except Exception as e:
                self.logger.error(f"Error checking address {address}: {e}")
        
        # Process and display changes
        if all_changes:
            self.logger.info(f"Found {len(all_changes)} position changes")
            
            for change in all_changes:
                message = self._format_position_change(change)
                self.logger.info(message)
            
            # Send Telegram notifications
            if self.config.ENABLE_TELEGRAM_ALERTS and self.telegram_notifier.enabled:
                try:
                    if len(all_changes) == 1:
                        # Send individual change
                        await self.telegram_notifier.send_position_change(all_changes[0])
                    else:
                        # Send multiple changes in one message
                        await self.telegram_notifier.send_multiple_changes(all_changes)
                except Exception as e:
                    self.logger.error(f"Failed to send Telegram notification: {e}")
                    self.logger.error("Continuing without Telegram notifications for this session")
            
            # Save updated positions
            self._save_positions()
        
        return all_changes
    
    async def run_monitoring(self):
        """Main monitoring loop"""
        if self.test_mode:
            return await self._run_test_monitoring()
            
        self.logger.info("Starting position monitoring...")
        self.logger.info(f"Tracking {len(self.config.TRACKED_ADDRESSES)} addresses")
        self.logger.info(f"Polling interval: {self.config.POLLING_INTERVAL} seconds")
        
        # Send startup notification
        if self.config.ENABLE_TELEGRAM_ALERTS:
            try:
                await self.telegram_notifier.send_startup_message()
            except Exception as e:
                self.logger.error(f"Failed to send startup notification: {e}")
        
        try:
            while True:
                try:
                    # Check all addresses
                    await self.check_all_addresses()
                    
                    # Wait for next check
                    await asyncio.sleep(self.config.POLLING_INTERVAL)
                    
                except KeyboardInterrupt:
                    self.logger.info("Monitoring stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    
                    # Send error notification
                    if self.config.ENABLE_TELEGRAM_ALERTS:
                        try:
                            await self.telegram_notifier.send_error_alert(str(e))
                        except:
                            pass  # Don't let Telegram errors break the loop
                    
                    # Wait a bit before retrying
                    await asyncio.sleep(10)
        
        finally:
            # Send shutdown notification
            if self.config.ENABLE_TELEGRAM_ALERTS:
                try:
                    await self.telegram_notifier.send_shutdown_message()
                except Exception as e:
                    self.logger.error(f"Failed to send shutdown notification: {e}")
    
    async def _run_test_monitoring(self):
        """Run monitoring in test mode with simulated data"""
        self.logger.info("🧪 Starting test monitoring with simulated data...")
        self.logger.info(f"Testing with {len(self.config.TRACKED_ADDRESSES)} addresses")
        
        # First, test the change detection logic
        self.test_position_change_detection()
        
        try:
            for cycle in range(4):  # Run 4 test cycles
                self.test_cycle = cycle
                self.logger.info(f"🧪 Test cycle {cycle + 1}/4")
                
                # Check all addresses with simulated data
                changes = await self.check_all_addresses()
                
                if changes:
                    self.logger.info(f"🧪 Simulated {len(changes)} position changes")
                else:
                    self.logger.info("🧪 No position changes in this cycle")
                
                # Wait a bit between cycles
                await asyncio.sleep(3)
                
        except KeyboardInterrupt:
            self.logger.info("🧪 Test monitoring stopped by user")
        
        self.logger.info("🧪 Test monitoring completed successfully!")
    
    def test_position_change_detection(self):
        """Test the position change detection logic with mock data"""
        self.logger.info("🧪 Testing position change detection logic...")
        
        # Create mock old positions
        old_positions = {
            "ETH": Position(
                symbol="ETH",
                size=Decimal("10"),
                side="long",
                entry_price=Decimal("2500"),
                market_value=Decimal("25000"),
                unrealized_pnl=Decimal("500"),
                timestamp=datetime.now()
            )
        }
        
        # Create mock new positions (ETH increased, BTC opened)
        new_positions = {
            "ETH": Position(
                symbol="ETH",
                size=Decimal("15"),
                side="long",
                entry_price=Decimal("2500"),
                market_value=Decimal("37500"),
                unrealized_pnl=Decimal("1250"),
                timestamp=datetime.now()
            ),
            "BTC": Position(
                symbol="BTC",
                size=Decimal("0.5"),
                side="long",
                entry_price=Decimal("45000"),
                market_value=Decimal("22500"),
                unrealized_pnl=Decimal("1000"),
                timestamp=datetime.now()
            )
        }
        
        # Test change detection
        test_address = "0x1234567890123456789012345678901234567890"
        changes = self._detect_changes(test_address, old_positions, new_positions)
        
        self.logger.info(f"✅ Detected {len(changes)} changes:")
        for change in changes:
            message = self._format_position_change(change)
            self.logger.info(f"  {message}")
        
        return changes 