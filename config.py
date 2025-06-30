# Configuration for Hyperliquid Whale Tracker
# This file contains the main settings for tracking positions

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the whale tracker"""
    
    # Hyperliquid API Configuration
    # Set to True for testnet, False for mainnet
    USE_TESTNET = os.getenv('USE_TESTNET', 'False').lower() == 'true'
    
    # API URLs
    MAINNET_URL = "https://api.hyperliquid.xyz"
    TESTNET_URL = "https://api.hyperliquid-testnet.xyz"
    
    # Get the appropriate API URL based on testnet setting
    API_URL = TESTNET_URL if USE_TESTNET else MAINNET_URL
    
    # List of wallet addresses to track
    # Add the addresses you want to monitor here
    TRACKED_ADDRESSES: List[str] = [
        # Example addresses - replace with actual addresses you want to track
        "0xcd5051944f780a621ee62e39e493c489668acf4d",
        "0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6",
        "0x8af700ba841f30e0a3fcb0ee4c4a9d223e1efa05"
        # Add more addresses here
        # "0x1234567890123456789012345678901234567890",
        # "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    ]
    
    # Tracking Settings
    # How often to check for position changes (in seconds)
    POLLING_INTERVAL = 30
    
    # Minimum position size to track (in USD)
    MIN_POSITION_SIZE = 1000
    
    # Minimum position change to notify (in USD)
    MIN_CHANGE_THRESHOLD = 500
    
    # Logging Settings
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE = "whale_tracker.log"
    
    # Data Storage
    # Directory to store position data
    DATA_DIR = "data"
    POSITIONS_FILE = f"{DATA_DIR}/positions.json"
    
    # Notification Settings
    ENABLE_CONSOLE_OUTPUT = True
    ENABLE_FILE_LOGGING = True
    
    # Telegram Bot Settings
    ENABLE_TELEGRAM_ALERTS = os.getenv('ENABLE_TELEGRAM_ALERTS', 'False').lower() == 'true'
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Telegram message settings
    TELEGRAM_SEND_SUMMARY = True  # Send daily summary
    TELEGRAM_SEND_POSITION_CHANGES = True  # Send individual position changes
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate the configuration settings"""
        if not cls.TRACKED_ADDRESSES:
            print("ERROR: No addresses configured for tracking!")
            print("Please add wallet addresses to TRACKED_ADDRESSES in config.py")
            return False
            
        if cls.POLLING_INTERVAL < 10:
            print("WARNING: Polling interval is very short. Consider using >= 10 seconds")
        
        # Validate Telegram settings if enabled
        if cls.ENABLE_TELEGRAM_ALERTS:
            if not cls.TELEGRAM_BOT_TOKEN:
                print("ERROR: Telegram alerts enabled but TELEGRAM_BOT_TOKEN not set!")
                print("Please set TELEGRAM_BOT_TOKEN in your .env file")
                return False
            
            if not cls.TELEGRAM_CHAT_ID:
                print("ERROR: Telegram alerts enabled but TELEGRAM_CHAT_ID not set!")
                print("Please set TELEGRAM_CHAT_ID in your .env file")
                return False
                
            print("✅ Telegram alerts configured")
            
        return True
    
    @classmethod
    def get_address_labels(cls) -> Dict[str, str]:
        """
        Define friendly labels for tracked addresses
        You can customize this to give meaningful names to addresses
        """
        return {
            "0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6": "James Wynn"
            # Example: "0xcd5051944f780a621ee62e39e493c489668acf4d": "Whale #1",
            # Add your own labels here
        } 