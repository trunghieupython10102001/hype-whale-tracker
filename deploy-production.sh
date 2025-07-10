#!/bin/bash

# Whale Tracker - Production Deployment Script
# This script deploys to production using docker-compose.prod.yml

set -e  # Exit on any error

echo "🚀 WHALE TRACKER - PRODUCTION DEPLOYMENT"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
if [ ! -f "docker-compose.prod.yml" ]; then
    print_error "docker-compose.prod.yml not found!"
    print_error "Please run this script from the whale-tracker directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_error "Production deployment requires .env file with configuration"
    print_error "See env_example.txt for reference"
    exit 1
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

# Stop existing containers using production config
print_status "Stopping existing production containers..."
docker compose -f docker-compose.prod.yml down || print_warning "Containers may not be running"

# Build new images
print_status "Building production Docker images..."
if docker compose -f docker-compose.prod.yml build --no-cache; then
    print_success "Images built successfully"
else
    print_error "Failed to build Docker images"
    exit 1
fi

# Start production services
print_status "Starting production services..."
if docker compose -f docker-compose.prod.yml up -d; then
    print_success "Production services started successfully!"
else
    print_error "Failed to start production services"
    exit 1
fi

# Wait for services to initialize
print_status "Waiting for services to initialize..."
sleep 15

# Check service status
print_status "Checking production service status..."
docker compose -f docker-compose.prod.yml ps

# Show recent logs
print_status "Showing recent production logs..."
echo ""
echo "🐋 WHALE TRACKER PRODUCTION LOGS:"
echo "================================="
docker compose -f docker-compose.prod.yml logs --tail=20 whale-tracker

echo ""
echo "🤖 COMMAND HANDLER PRODUCTION LOGS:"
echo "==================================="
docker compose -f docker-compose.prod.yml logs --tail=20 whale-commands

# Health check
print_status "Performing health check..."
sleep 5
if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_success "✅ Production deployment completed successfully!"
else
    print_error "❌ Some services may not be running properly"
    docker compose -f docker-compose.prod.yml ps
fi

echo ""
print_status "📋 Production management commands:"
echo "  • View live logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  • Check status: docker compose -f docker-compose.prod.yml ps"
echo "  • Stop services: docker compose -f docker-compose.prod.yml down"
echo "  • Restart: docker compose -f docker-compose.prod.yml restart"
echo ""
print_status "🔍 Monitor whale alerts in your Telegram bot!"
print_warning "🛡️  Remember to monitor server resources and logs in production" 