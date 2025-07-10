# 🐋 EC2 Deployment Guide - Hyperliquid Whale Tracker

This guide will help you deploy the Hyperliquid Whale Tracker on an AWS EC2 instance using Docker.

## 📋 Prerequisites

- AWS Account with EC2 access
- Basic familiarity with AWS Console and SSH
- Your Telegram bot token and chat ID (optional but recommended)

## 🚀 Step 1: Launch EC2 Instance

### Instance Configuration
1. **Go to AWS EC2 Console**
2. **Click "Launch Instance"**
3. **Choose AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
4. **Instance Type**: t2.micro (Free tier) or t3.small (Recommended for better performance)
5. **Key Pair**: Create a new key pair or use existing one
6. **Security Group**: Create new with the following rules:
   - SSH (22) - Your IP only
   - HTTPS (443) - 0.0.0.0/0 (for API access)
   - HTTP (80) - 0.0.0.0/0 (for API access)

### Storage
- **Root volume**: 20 GB gp3 (minimum 10 GB)

### Advanced Details
- **User data** (optional - for automatic setup):
```bash
#!/bin/bash
apt-get update -y
apt-get install -y git
```

## 🔧 Step 2: Connect to Your Instance

```bash
# Replace with your key file and instance IP
ssh -i "your-key.pem" ubuntu@your-ec2-ip
```

## 📦 Step 3: Upload Your Code

### Option A: Using SCP (from your local machine)
```bash
# Create a tar file of your project (run locally)
tar -czf whale-tracker.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.log' .

# Upload to EC2 (run locally)
scp -i "your-key.pem" whale-tracker.tar.gz ubuntu@your-ec2-ip:~/

# Extract on EC2 (run on EC2)
ssh -i "your-key.pem" ubuntu@your-ec2-ip
cd ~
tar -xzf whale-tracker.tar.gz
mv whale-tracker-* whale-tracker  # if needed
```

### Option B: Using Git (recommended)
```bash
# On your EC2 instance
git clone https://github.com/your-username/whale-tracker.git
cd whale-tracker
```

## 🐳 Step 4: Run Deployment Script

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

The script will:
- Install Docker and Docker Compose
- Create necessary directories
- Set up the application
- Create a template `.env` file

## ⚙️ Step 5: Configure Environment

### Edit your `.env` file:
```bash
nano ~/whale-tracker/.env
```

### Update with your values:
```env
# Telegram Bot Configuration
ENABLE_TELEGRAM_ALERTS=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Hyperliquid Configuration
USE_TESTNET=false
POLLING_INTERVAL=30
MIN_POSITION_SIZE=1000
MIN_CHANGE_THRESHOLD=500

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_CONSOLE_OUTPUT=true
ENABLE_FILE_LOGGING=true
```

### Update tracked addresses in `config.py`:
```bash
nano ~/whale-tracker/config.py
```

## 🚦 Step 6: Start the Application

```bash
cd ~/whale-tracker

# Build and start
docker compose up -d

# Check if running
docker compose ps

# View logs
docker compose logs -f
```

## 📊 Step 7: Monitor and Manage

### Useful Commands:
```bash
# Check status
docker compose ps

# View live logs
docker compose logs -f

# Restart service
docker compose restart

# Stop service
docker compose down

# Update and restart
docker compose build && docker compose up -d

# View container resource usage
docker stats

# Access container shell (for debugging)
docker compose exec whale-tracker bash
```

### Check Application Health:
```bash
# Test network connectivity
docker compose exec whale-tracker python3 main.py --test-network

# Run in test mode
docker compose exec whale-tracker python3 main.py --test-mode
```

## 🔒 Step 8: Security Best Practices

### 1. Update Security Group
After deployment, restrict SSH access to your IP only:
```
SSH (22) - Your specific IP/32
```

### 2. Set up automatic updates
```bash
# Enable automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Set up log rotation
```bash
# Docker handles log rotation, but you can also set up system-wide
sudo logrotate -d /etc/logrotate.conf
```

## 📈 Step 9: Performance Optimization

### For High-Volume Monitoring:
1. **Upgrade to t3.small** or larger instance
2. **Increase polling interval** if needed
3. **Add more storage** if logging heavily

### Resource Monitoring:
```bash
# Check system resources
htop
df -h
free -h

# Check Docker container resources
docker stats
```

## 🔄 Step 10: Backup and Maintenance

### Backup Important Data:
```bash
# Backup position data
cp ~/whale-tracker/data/positions.json ~/backup/
cp ~/whale-tracker/.env ~/backup/

# Or create automated backup script
crontab -e
# Add: 0 2 * * * cp ~/whale-tracker/data/positions.json ~/backup/positions-$(date +\%Y\%m\%d).json
```

### Update Application:
```bash
cd ~/whale-tracker
git pull origin main
docker compose build
docker compose up -d
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Container won't start**:
   ```bash
   docker compose logs
   # Check for configuration errors
   ```

2. **Permission denied**:
   ```bash
   sudo chmod -R 755 ~/whale-tracker/data
   sudo chown -R $(whoami):$(whoami) ~/whale-tracker/
   ```

3. **Out of disk space**:
   ```bash
   # Clean up Docker
   docker system prune -a
   
   # Clean up logs
   docker compose down
   rm -rf ~/whale-tracker/logs/*
   docker compose up -d
   ```

4. **Network connectivity issues**:
   ```bash
   # Test from inside container
   docker compose exec whale-tracker curl -I https://api.hyperliquid.xyz
   docker compose exec whale-tracker curl -I https://api.telegram.org
   ```

### Emergency Recovery:
```bash
# Stop everything
docker compose down

# Remove containers and images
docker system prune -a

# Rebuild from scratch
./deploy.sh
```

## 💰 Cost Estimation

### EC2 Costs (US-East-1):
- **t2.micro**: ~$8.50/month (Free tier: 750 hours/month free for 12 months)
- **t3.small**: ~$15/month 
- **Storage**: ~$2/month for 20GB

### Total Monthly Cost:
- **Free tier**: ~$2/month (storage only)
- **Production**: ~$17/month (t3.small + storage)

## 🎯 Production Checklist

- [ ] EC2 instance launched with proper security group
- [ ] SSH access restricted to your IP
- [ ] Application deployed and running
- [ ] Environment variables configured
- [ ] Telegram notifications working
- [ ] Logs are being generated
- [ ] Backup strategy in place
- [ ] Monitoring alerts set up

## 📞 Support

If you encounter issues:
1. Check the logs: `docker compose logs -f`
2. Test connectivity: `python3 main.py --test-network`
3. Verify configuration: Check your `.env` file
4. Review this guide for missed steps

Your whale tracker should now be running 24/7 on EC2! 🎉 