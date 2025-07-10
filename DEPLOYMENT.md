# Whale Tracker - Deployment Guide

This guide explains how to use the deployment scripts for the Whale Tracker application.

## 🔧 Available Scripts

### 1. `update-and-restart.sh` - Full Update & Restart
**When to use:** When you need to pull the latest changes from GitHub and restart all services.

```bash
./update-and-restart.sh
```

**What it does:**
- ✅ Backs up your data directory 
- ✅ Pulls latest changes from GitHub
- ✅ Stops existing Docker containers
- ✅ Rebuilds Docker images with latest code
- ✅ Starts services with updated code
- ✅ Shows logs and service status

### 2. `quick-restart.sh` - Quick Restart Only
**When to use:** When you just need to restart services without updating code.

```bash
./quick-restart.sh
```

**What it does:**
- ✅ Restarts Docker services quickly
- ✅ Shows service status
- ✅ No code updates, no rebuilds

### 3. `deploy-production.sh` - Production Deployment
**When to use:** For production deployments on EC2 or production servers.

```bash
./deploy-production.sh
```

**What it does:**
- ✅ Uses `docker-compose.prod.yml` configuration
- ✅ Backs up data directory
- ✅ Pulls latest changes
- ✅ Builds production Docker images
- ✅ Starts production services
- ✅ Performs health checks
- ✅ Shows production logs

## 📋 Prerequisites

### Required Files
- `.env` file with your configuration (see `env_example.txt`)
- `docker-compose.yml` for development
- `docker-compose.prod.yml` for production

### Required Software
- Docker and Docker Compose
- Git (configured with access to the repository)

## 🛡️ Data Safety

All scripts automatically create backups of your `data/` directory before making changes:
- Backup format: `data_backup_YYYYMMDD_HHMMSS`
- Contains: user chat IDs, dynamic addresses, position data

## 🚨 Troubleshooting

### Common Issues

**1. Permission Denied**
```bash
chmod +x *.sh
```

**2. Docker Not Running**
```bash
# Start Docker service
sudo systemctl start docker  # Linux
# Or start Docker Desktop on macOS/Windows
```

**3. Git Pull Fails**
- Check internet connection
- Verify git credentials
- Make sure you're in the correct directory

**4. Environment File Missing**
```bash
cp env_example.txt .env
# Edit .env with your configuration
```

### Monitoring Commands

After deployment, use these commands to monitor your application:

```bash
# View live logs
docker-compose logs -f

# Check service status  
docker-compose ps

# Restart specific service
docker-compose restart whale-tracker

# Stop all services
docker-compose down
```

### Production Monitoring

For production deployments:

```bash
# View production logs
docker-compose -f docker-compose.prod.yml logs -f

# Check production status
docker-compose -f docker-compose.prod.yml ps

# Restart production services
docker-compose -f docker-compose.prod.yml restart
```

## 🔄 Typical Workflow

### Development Updates
1. Make code changes locally
2. Test changes
3. Push to GitHub
4. Run `./update-and-restart.sh` on server

### Production Deployment
1. Test changes in development
2. Push to GitHub
3. Run `./deploy-production.sh` on production server
4. Monitor logs and alerts

### Quick Fixes
1. If services are running but not responding properly
2. Run `./quick-restart.sh`
3. Check logs for issues

## ⚡ Pro Tips

- **Always backup data:** Scripts do this automatically, but keep additional backups
- **Monitor logs:** After deployment, watch logs for a few minutes to ensure everything works
- **Test first:** Use development environment before production deployment
- **Environment specific:** Use appropriate script for your environment (dev vs prod)

## 🆘 Emergency Recovery

If deployment fails:

1. **Check service status:**
   ```bash
   docker-compose ps
   ```

2. **View error logs:**
   ```bash
   docker-compose logs --tail=50
   ```

3. **Restore from backup:**
   ```bash
   # Stop services
   docker-compose down
   
   # Restore data
   rm -rf data/
   cp -r data_backup_YYYYMMDD_HHMMSS/ data/
   
   # Restart services
   docker-compose up -d
   ```

4. **Contact support** if issues persist 