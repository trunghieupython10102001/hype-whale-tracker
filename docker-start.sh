#!/bin/bash
# Docker Startup Script for Whale Tracker
# This script helps you start the whale tracker with proper configuration

set -e

echo "🐋 Hyperliquid Whale Tracker - Docker Startup"
echo "=============================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📋 Creating .env from template..."
    
    if [ -f .env.docker ]; then
        cp .env.docker .env
        echo "✅ Created .env from .env.docker template"
        echo "📝 Please edit .env with your configuration:"
        echo "   - TELEGRAM_BOT_TOKEN"
        echo "   - TELEGRAM_CHAT_ID"
        echo "   - POLLING_INTERVAL (currently: 10 seconds)"
        echo "   - MIN_POSITION_SIZE (currently: $1000)"
        echo "   - MIN_CHANGE_THRESHOLD (currently: $500)"
        echo ""
        echo "🔧 Edit .env file and run this script again"
        exit 1
    else
        echo "❌ No .env.docker template found!"
        echo "Please create .env file manually"
        exit 1
    fi
fi

# Source .env to check configuration
source .env

# Validate required variables
echo "🔍 Validating configuration..."

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not configured in .env"
    exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_CHAT_ID" = "your_chat_id_here" ]; then
    echo "❌ TELEGRAM_CHAT_ID not configured in .env"
    exit 1
fi

# Show current configuration
echo "✅ Configuration validated!"
echo "📊 Current settings:"
echo "   🔔 Telegram alerts: ${ENABLE_TELEGRAM_ALERTS:-true}"
echo "   🌐 Use testnet: ${USE_TESTNET:-false}"
echo "   ⏱️  Polling interval: ${POLLING_INTERVAL:-10} seconds"
echo "   💰 Min position size: $${MIN_POSITION_SIZE:-1000}"
echo "   📈 Min change threshold: $${MIN_CHANGE_THRESHOLD:-500}"
echo "   📝 Log level: ${LOG_LEVEL:-INFO}"
echo ""

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data logs

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker and try again"
    exit 1
fi

# Parse command line arguments
COMPOSE_FILES="-f docker-compose.yml"
DETACHED=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|--production)
            COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.prod.yml"
            echo "🏭 Production mode enabled"
            shift
            ;;
        --dev|--development)
            echo "🔧 Development mode enabled"
            shift
            ;;
        -d|--detached)
            DETACHED="-d"
            echo "🔄 Running in detached mode"
            shift
            ;;
        --stop)
            echo "🛑 Stopping whale tracker..."
            docker compose $COMPOSE_FILES down
            exit 0
            ;;
        --logs)
            echo "📄 Showing logs..."
            docker compose $COMPOSE_FILES logs -f
            exit 0
            ;;
        --status)
            echo "📊 Service status:"
            docker compose $COMPOSE_FILES ps
            exit 0
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --prod, --production    Use production configuration"
            echo "  --dev, --development    Use development configuration (default)"
            echo "  -d, --detached         Run in background"
            echo "  --stop                 Stop all services"
            echo "  --logs                 Show service logs"
            echo "  --status               Show service status"
            echo "  -h, --help             Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                     Start in development mode"
            echo "  $0 --prod -d           Start in production mode, detached"
            echo "  $0 --stop              Stop all services"
            echo "  $0 --logs              View logs"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use $0 --help for usage information"
            exit 1
            ;;
    esac
done

# Build and start services
echo "🚀 Starting whale tracker services..."
echo "📋 Services starting:"
echo "   📊 whale-tracker (main monitoring)"
echo "   🤖 whale-commands (Telegram commands)"
echo ""

# Build if needed
docker compose $COMPOSE_FILES build

# Start services
docker compose $COMPOSE_FILES up $DETACHED

if [ -n "$DETACHED" ]; then
    echo "✅ Services started in background!"
    echo ""
    echo "📋 Useful commands:"
    echo "   $0 --logs     - View logs"
    echo "   $0 --status   - Check status"
    echo "   $0 --stop     - Stop services"
    echo ""
    echo "🤖 Try these Telegram commands:"
    echo "   /help - Show available commands"
    echo "   /list - Show tracked addresses"
    echo "   /add 0x....:Label - Add new address"
else
    echo ""
    echo "Press Ctrl+C to stop the services"
fi 