#!/usr/bin/env python3
"""
Hyperliquid Whale Tracker - Main Application
Monitor position changes for specific addresses on Hyperliquid
"""

import asyncio
import signal
import sys
import argparse
from position_tracker import HyperliquidTracker
from utils import test_network_connectivity, test_telegram_bot


def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) gracefully"""
    print("\n🛑 Shutdown signal received. Stopping tracker...")
    sys.exit(0)


def display_startup_info():
    """Display startup information and configuration"""
    print("=" * 60)
    print("🐋 HYPERLIQUID WHALE TRACKER")
    print("=" * 60)
    print("📊 Monitor position changes for tracked addresses")
    print("💬 Get real-time alerts via Telegram")
    print("🔍 Track opens, closes, increases, and decreases")
    print("=" * 60)


async def main():
    """Main application function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hyperliquid Whale Tracker')
    parser.add_argument('--test-mode', action='store_true', 
                       help='Run in test mode with simulated data (no network required)')
    parser.add_argument('--test-hyperliquid', action='store_true',
                       help='Test Hyperliquid API connectivity')
    parser.add_argument('--test-telegram', action='store_true',
                       help='Test Telegram bot connectivity')
    parser.add_argument('--test-addresses', action='store_true',
                       help='Test address format validation')
    parser.add_argument('--test-network', action='store_true',
                       help='Test network connectivity to required services')
    
    args = parser.parse_args()
    
    # Handle test commands
    if args.test_addresses:
        print("🔍 Address format testing:")
        print("   Run: python3 utils.py test <address1> <address2> ...")
        print("   Or:  python3 utils.py test-config")
        return
    
    if args.test_network:
        await test_network_connectivity()
        return
    
    if args.test_telegram:
        await test_telegram_bot()
        return
    
    # Display startup info
    display_startup_info()
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Initialize tracker with test mode if specified
        test_mode = args.test_mode
        if test_mode:
            print("🧪 Running in TEST MODE - using simulated data")
            print("📋 This will demonstrate position change detection without network connectivity")
            print()
        
        tracker = HyperliquidTracker(test_mode=test_mode)
        
        # Check if Telegram alerts are configured
        from config import Config
        if Config.ENABLE_TELEGRAM_ALERTS:
            if Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_CHAT_ID:
                print("✅ Telegram alerts configured")
            else:
                print("⚠️  Telegram alerts enabled but credentials missing")
                print("   Please check your .env file or disable in config.py")
        else:
            print("ℹ️  Telegram alerts disabled")
        
        print()
        
        # Initialize the tracker
        if not test_mode:
            print("🔗 Connecting to Hyperliquid API...")
            await tracker.initialize()
            print("✅ Connected successfully")
        
        # Handle test-hyperliquid command
        if args.test_hyperliquid:
            if test_mode:
                print("🧪 Test mode enabled - skipping network tests")
            else:
                print("🔍 Testing Hyperliquid API connection...")
                return
        
        print()
        
        # Start monitoring
        await tracker.run_monitoring()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to initialize tracker: {e}")
        
        if not test_mode:
            print("\n💡 Tips:")
            print("   • Check your internet connection")
            print("   • Verify firewall settings")
            print("   • Try running with --test-mode to test offline")
            print("   • Run 'python3 main.py --test-network' for diagnostics")
        
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 