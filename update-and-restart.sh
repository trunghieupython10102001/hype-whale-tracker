#!/bin/bash

# Whale Tracker - Update and Restart Script
# This script pulls latest changes and restarts docker compose services

set -e  # Exit on any error

echo "🐋 WHALE TRACKER - UPDATE AND RESTART"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
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

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found!"
    print_warning "Make sure to create .env file with your configuration"
    print_warning "See env_example.txt for reference"
fi

# Backup data directory if it exists
if [ -d "data" ]; then
    print_status "Creating backup of data directory..."
    backup_dir="data_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r data "$backup_dir"
    print_success "Data backed up to: $backup_dir"
fi

# Pull latest changes from git
print_status "Pulling latest changes from GitHub..."
if git pull origin main; then
    print_success "Successfully pulled latest changes"
else
    print_error "Failed to pull changes from git"
    print_error "Please check your git configuration and network connection"
    exit 1
fi

# Stop existing containers
print_status "Stopping existing Docker containers..."
if docker-compose down; then
    print_success "Containers stopped successfully"
else
    print_warning "Failed to stop containers (they may not be running)"
fi

# Remove old images to force rebuild
print_status "Removing old Docker images to force rebuild..."
docker-compose build --no-cache || {
    print_warning "Failed to build with --no-cache, trying regular build..."
    docker-compose build
}

# Start services
print_status "Starting updated services..."
if docker-compose up -d; then
    print_success "Services started successfully!"
else
    print_error "Failed to start services"
    exit 1
fi

# Wait a moment for services to initialize
print_status "Waiting for services to initialize..."
sleep 10

# Check service status
print_status "Checking service status..."
docker-compose ps

# Show recent logs
print_status "Showing recent logs (last 20 lines)..."
echo ""
echo "🐋 WHALE TRACKER LOGS:"
echo "====================="
docker-compose logs --tail=20 whale-tracker

echo ""
echo "🤖 COMMAND HANDLER LOGS:"
echo "========================"
docker-compose logs --tail=20 whale-commands

echo ""
print_success "✅ Update and restart completed successfully!"
echo ""
print_status "📋 Useful commands:"
echo "  • View live logs: docker-compose logs -f"
echo "  • Check status: docker-compose ps"
echo "  • Stop services: docker-compose down"
echo "  • Restart: docker-compose restart"
echo ""
print_status "🔍 Monitor whale alerts in your Telegram bot!" 