#!/usr/bin/env python3
"""
Fix MySQL localhost connection for Replit
Creates a tunnel to local MySQL server
"""

import os
import subprocess
import logging
import time
import socket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ngrok_installed():
    """Check if ngrok is available"""
    try:
        result = subprocess.run(['which', 'ngrok'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def install_ngrok():
    """Install ngrok in Replit environment"""
    logger.info("Installing ngrok...")
    try:
        # Download and install ngrok
        subprocess.run(['wget', 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz'], check=True)
        subprocess.run(['tar', '-xzf', 'ngrok-v3-stable-linux-amd64.tgz'], check=True)
        subprocess.run(['chmod', '+x', 'ngrok'], check=True)
        logger.info("✅ ngrok installed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to install ngrok: {e}")
        return False

def create_mysql_tunnel():
    """Create tunnel to local MySQL"""
    logger.info("🔧 Setting up MySQL tunnel solution...")
    
    # Check if ngrok is available
    if not check_ngrok_installed():
        logger.info("ngrok not found, installing...")
        if not install_ngrok():
            return False
    
    logger.info("📋 MySQL Tunnel Setup Instructions:")
    logger.info("="*50)
    logger.info("")
    logger.info("🏠 On your LOCAL machine (where MySQL is running):")
    logger.info("1. Download ngrok from https://ngrok.com")
    logger.info("2. Run this command:")
    logger.info("   ngrok tcp 3306")
    logger.info("3. Copy the forwarding URL (e.g., 0.tcp.ngrok.io:12345)")
    logger.info("")
    logger.info("☁️ In Replit:")
    logger.info("4. Update your Secrets with the ngrok URL")
    logger.info("5. Test connection with: python mysql_complete_migration.py")
    logger.info("")
    
    return True

def update_env_for_tunnel():
    """Update environment configuration for tunnel"""
    logger.info("📝 Creating tunnel configuration template...")
    
    tunnel_config = """
# MySQL Tunnel Configuration
# After setting up ngrok on your local machine, update these values:

# MYSQL_HOST=0.tcp.ngrok.io  # Replace with your ngrok URL
# MYSQL_PORT=12345           # Replace with your ngrok port
MYSQL_USER=root
MYSQL_PASSWORD=root@123
MYSQL_DATABASE=wms_db_dev

# Example ngrok command for your local machine:
# ngrok tcp 3306
"""
    
    with open('.env.tunnel', 'w') as f:
        f.write(tunnel_config)
    
    logger.info("✅ Created .env.tunnel template")
    logger.info("📋 After setting up ngrok, copy values from .env.tunnel to your Replit Secrets")

if __name__ == "__main__":
    logger.info("🚀 MySQL Localhost Fix for Replit")
    logger.info("="*40)
    
    create_mysql_tunnel()
    update_env_for_tunnel()
    
    logger.info("")
    logger.info("🎯 Next Steps:")
    logger.info("1. Run ngrok on your local machine")
    logger.info("2. Update Replit Secrets with ngrok URL")
    logger.info("3. Restart your application")
    logger.info("4. All data will flow to your local MySQL!")