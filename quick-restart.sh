#!/bin/bash

# Whale Tracker - Quick Restart Script
# This script restarts docker compose services without pulling new changes

set -e  # Exit on any error

echo "🐋 WHALE TRACKER - QUICK RESTART"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found!"
    print_error "Please run this script from the whale-tracker directory"
    exit 1
fi

# Restart services
print_status "Restarting Docker services..."
if docker-compose restart; then
    print_success "Services restarted successfully!"
else
    print_error "Failed to restart services"
    exit 1
fi

# Wait a moment for services to initialize
print_status "Waiting for services to initialize..."
sleep 5

# Check service status
print_status "Checking service status..."
docker-compose ps

print_success "✅ Quick restart completed!"
print_status "🔍 Monitor whale alerts in your Telegram bot!" 