"""
Utility functions for the Hyperliquid Whale Tracker
"""

import asyncio
import sys
from typing import List, Dict, Any, Optional
from decimal import Decimal

from hyperliquid.info import Info
from config import Config
from telegram_bot import get_telegram_notifier


class TrackerUtils:
    """Utility class for tracker operations"""
    
    def __init__(self):
        self.info_client = None
    
    async def initialize(self):
        """Initialize the API client"""
        try:
            self.info_client = Info(Config.API_URL, skip_ws=True)
            print(f"✅ Connected to {Config.API_URL}")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise
    
    def validate_address(self, address: str) -> bool:
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
    
    async def check_address_activity(self, address: str) -> Dict[str, Any]:
        """Check if an address has any trading activity on Hyperliquid"""
        try:
            user_state = self.info_client.user_state(address)
            
            result = {
                'address': address,
                'valid': True,
                'has_positions': False,
                'position_count': 0,
                'total_value': Decimal('0'),
                'positions': []
            }
            
            if user_state and 'assetPositions' in user_state:
                active_positions = []
                total_value = Decimal('0')
                
                for pos_data in user_state['assetPositions']:
                    position = pos_data['position']
                    
                    # Skip zero positions
                    if float(position['szi']) == 0:
                        continue
                    
                    symbol = position['coin']
                    size = Decimal(position['szi'])
                    entry_price = Decimal(position['entryPx']) if position['entryPx'] else Decimal('0')
                    unrealized_pnl = Decimal(position['unrealizedPnl'])
                    
                    market_value = abs(size) * entry_price
                    total_value += market_value
                    
                    side = "long" if size > 0 else "short"
                    
                    active_positions.append({
                        'symbol': symbol,
                        'side': side,
                        'size': str(abs(size)),
                        'entry_price': str(entry_price),
                        'market_value': str(market_value),
                        'unrealized_pnl': str(unrealized_pnl)
                    })
                
                result['has_positions'] = len(active_positions) > 0
                result['position_count'] = len(active_positions)
                result['total_value'] = total_value
                result['positions'] = active_positions
            
            return result
            
        except Exception as e:
            return {
                'address': address,
                'valid': False,
                'error': str(e),
                'has_positions': False,
                'position_count': 0,
                'total_value': Decimal('0'),
                'positions': []
            }
    
    async def test_addresses(self, addresses: List[str]) -> List[Dict[str, Any]]:
        """Test multiple addresses and return their status"""
        results = []
        
        print(f"🔍 Testing {len(addresses)} addresses...")
        print("-" * 60)
        
        for i, address in enumerate(addresses, 1):
            print(f"Testing {i}/{len(addresses)}: {address[:10]}...")
            
            # Validate address format
            if not self.validate_address(address):
                results.append({
                    'address': address,
                    'valid': False,
                    'error': 'Invalid address format',
                    'has_positions': False,
                    'position_count': 0,
                    'total_value': Decimal('0'),
                    'positions': []
                })
                continue
            
            # Check activity
            result = await self.check_address_activity(address)
            results.append(result)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        return results
    
    def print_address_report(self, results: List[Dict[str, Any]]):
        """Print a formatted report of address testing results"""
        print("\n" + "="*80)
        print("📊 ADDRESS TESTING REPORT")
        print("="*80)
        
        valid_count = sum(1 for r in results if r['valid'])
        active_count = sum(1 for r in results if r['has_positions'])
        total_value = sum(r['total_value'] for r in results if r['valid'])
        
        print(f"✅ Valid addresses: {valid_count}/{len(results)}")
        print(f"📈 Addresses with positions: {active_count}/{len(results)}")
        print(f"💰 Total position value: ${total_value:,.2f}")
        print()
        
        for result in results:
            address = result['address']
            short_addr = f"{address[:6]}...{address[-4:]}"
            
            if not result['valid']:
                print(f"❌ {short_addr}: {result.get('error', 'Invalid')}")
                continue
            
            if result['has_positions']:
                print(f"🟢 {short_addr}: {result['position_count']} positions, ${result['total_value']:,.2f}")
                for pos in result['positions']:
                    print(f"   └─ {pos['symbol']} {pos['side'].upper()}: ${pos['market_value']}")
            else:
                print(f"⚪ {short_addr}: No active positions")
        
        print("\n" + "="*80)
        
        if active_count > 0:
            print("✅ Ready to track! Add these addresses to config.py")
        else:
            print("⚠️  No addresses with active positions found.")
            print("   Try adding addresses of known active traders.")


async def test_network_connectivity():
    """Test basic network connectivity to required services"""
    print("🌐 Testing Network Connectivity...")
    print("-" * 60)
    
    import subprocess
    import sys
    
    services = {
        'Hyperliquid API': 'https://api.hyperliquid.xyz',
        'Telegram API': 'https://api.telegram.org'
    }
    
    results = {}
    
    for service_name, url in services.items():
        try:
            result = subprocess.run(
                ['curl', '-s', '--connect-timeout', '10', url],
                capture_output=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print(f"✅ Can reach {service_name}")
                results[service_name] = True
            else:
                print(f"❌ Cannot reach {service_name}")
                print(f"   curl exit code: {result.returncode}")
                results[service_name] = False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Connection timeout to {service_name}")
            results[service_name] = False
        except FileNotFoundError:
            print("ℹ️  curl not available for testing")
            return None
        except Exception as e:
            print(f"❌ Network test error for {service_name}: {e}")
            results[service_name] = False
    
    print("\n🔍 Summary:")
    all_ok = all(results.values())
    if all_ok:
        print("✅ All services reachable")
    else:
        print("⚠️  Some services unreachable")
        if not results.get('Hyperliquid API', False):
            print("   - Hyperliquid API unreachable: Main functionality won't work")
        if not results.get('Telegram API', False):
            print("   - Telegram API unreachable: Notifications won't work")
    
    return results


async def test_telegram_bot():
    """Test Telegram bot configuration and connection"""
    print("🤖 Testing Telegram Bot Configuration...")
    print("-" * 60)
    
    # First test network connectivity
    network_results = await test_network_connectivity()
    if network_results is None:
        print("\n⚠️  Cannot test network connectivity (curl not available)")
    elif not network_results.get('Telegram API', False):
        print("\n⚠️  Telegram API unreachable.")
        print("   Telegram notifications will not work in this environment.")
        print("   The whale tracker will still work without Telegram notifications.")
        print("\n💡 Suggestions:")
        print("   - Try from a different network")
        print("   - Check firewall/proxy settings")
        print("   - Contact your network administrator")
        return
    
    # Check if Telegram alerts are enabled
    if not Config.ENABLE_TELEGRAM_ALERTS:
        print("❌ Telegram alerts are disabled")
        print("   Set ENABLE_TELEGRAM_ALERTS=true in your .env file")
        return
    
    # Check bot token
    if not Config.TELEGRAM_BOT_TOKEN or Config.TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
        print("❌ Bot token not configured")
        print("   Set TELEGRAM_BOT_TOKEN in your .env file")
        return
    
    # Check chat ID
    if not Config.TELEGRAM_CHAT_ID or Config.TELEGRAM_CHAT_ID == 'your_chat_id_here':
        print("❌ Chat ID not configured")
        print("   Set TELEGRAM_CHAT_ID in your .env file")
        return
    
    # Test bot connection
    try:
        notifier = get_telegram_notifier()
        
        if not notifier.enabled:
            print("❌ Telegram notifier failed to initialize")
            print("   Check the logs for more details")
            return
    except Exception as e:
        print(f"❌ Error creating notifier: {e}")
        return
    
    print(f"✅ Bot token: {Config.TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"✅ Chat ID: {Config.TELEGRAM_CHAT_ID}")
    
    # Test connection
    try:
        print("🔄 Testing connection to Telegram...")
        success = await notifier.test_connection()
        if success:
            print("✅ Telegram bot test successful!")
            print("   Check your Telegram chat for the test message")
        else:
            print("❌ Telegram bot test failed")
            print("\n🔧 Troubleshooting:")
            print("   1. Check your bot token is correct")
            print("   2. Verify your chat ID is correct")
            print("   3. Make sure you've sent a message to your bot first")
            print("   4. Check network connectivity to api.telegram.org")
            print("   5. Verify no firewall/proxy is blocking HTTPS connections")
    except Exception as e:
        print(f"❌ Telegram test error: {e}")
        print("\n🌐 Network Issues:")
        print("   - Check internet connectivity")
        print("   - Verify HTTPS connections are allowed")
        print("   - Check if corporate firewall blocks Telegram")
        print("   - Try from a different network if possible")


async def main():
    """Main function for running utilities"""
    if len(sys.argv) < 2:
        print("""
🛠️ Hyperliquid Whale Tracker Utilities

Usage:
python utils.py test <address1> <address2> ...    # Test specific addresses
python utils.py test-config                       # Test addresses from config.py
python utils.py test-telegram                     # Test Telegram bot configuration
python utils.py test-network                      # Test network connectivity

Examples:
python utils.py test 0xcd5051944f780a621ee62e39e493c489668acf4d
python utils.py test-config
python utils.py test-telegram
python utils.py test-network
""")
        return
    
    command = sys.argv[1]
    
    if command == "test-telegram":
        await test_telegram_bot()
        return
    
    if command == "test-network":
        results = await test_network_connectivity()
        if results:
            hyperliquid_ok = results.get('Hyperliquid API', False)
            telegram_ok = results.get('Telegram API', False)
            
            print(f"\n📊 Network Status:")
            print(f"   Hyperliquid: {'✅ OK' if hyperliquid_ok else '❌ BLOCKED'}")
            print(f"   Telegram:    {'✅ OK' if telegram_ok else '❌ BLOCKED'}")
            
            if not hyperliquid_ok:
                print(f"\n⚠️  Cannot run whale tracker without Hyperliquid API access")
            elif not telegram_ok:
                print(f"\n✅ Can run whale tracker (without Telegram notifications)")
            else:
                print(f"\n✅ All systems ready!")
        return
    
    utils = TrackerUtils()
    
    try:
        await utils.initialize()
        
        if command == "test":
            if len(sys.argv) < 3:
                print("❌ Please provide at least one address to test")
                return
            
            addresses = sys.argv[2:]
            results = await utils.test_addresses(addresses)
            utils.print_address_report(results)
        
        elif command == "test-config":
            if not Config.TRACKED_ADDRESSES:
                print("❌ No addresses configured in config.py")
                return
            
            results = await utils.test_addresses(Config.TRACKED_ADDRESSES)
            utils.print_address_report(results)
        
        else:
            print(f"❌ Unknown command: {command}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 