#!/bin/bash
# Whale Tracker Startup Script
# This script starts both the main tracker and Telegram command handler

echo "🐋 Starting Whale Tracker System..."
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your configuration"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping whale tracker..."
    jobs -p | xargs -r kill
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start main tracker in background
echo "🚀 Starting main tracker..."
python3 main.py > logs/tracker.log 2>&1 &
TRACKER_PID=$!

# Wait a moment for tracker to initialize
sleep 3

# Start command handler in background
echo "🤖 Starting Telegram command handler..."
python3 telegram_command_handler.py > logs/command_handler.log 2>&1 &
HANDLER_PID=$!

echo "✅ Both services started successfully!"
echo "📊 Main tracker PID: $TRACKER_PID"
echo "🤖 Command handler PID: $HANDLER_PID"
echo ""
echo "📋 Available Telegram commands:"
echo "   /add address:label - Add new address"
echo "   /remove address - Remove address"
echo "   /list - Show tracked addresses"
echo "   /help - Show help"
echo ""
echo "📄 Logs:"
echo "   Main tracker: logs/tracker.log"
echo "   Command handler: logs/command_handler.log"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for background processes
wait 