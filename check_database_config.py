#!/usr/bin/env python3
"""
Check current database configuration and provide guidance
"""

import os
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_config():
    """Check current database configuration"""
    logger.info("🔍 Current Database Configuration:")
    logger.info("="*50)
    
    # Check MySQL config
    mysql_host = os.environ.get("MYSQL_HOST")
    mysql_user = os.environ.get("MYSQL_USER") 
    mysql_password = os.environ.get("MYSQL_PASSWORD")
    mysql_database = os.environ.get("MYSQL_DATABASE")
    database_url = os.environ.get("DATABASE_URL")
    
    logger.info("📊 MySQL Configuration:")
    logger.info(f"  Host: {mysql_host}")
    logger.info(f"  User: {mysql_user}")
    logger.info(f"  Database: {mysql_database}")
    logger.info(f"  Password: {'*' * len(mysql_password) if mysql_password else 'None'}")
    
    logger.info(f"\n🐘 PostgreSQL Configuration:")
    logger.info(f"  DATABASE_URL: {'Set' if database_url else 'Not set'}")
    
    logger.info("\n🎯 Current Status:")
    if mysql_host and mysql_host.lower() in ['localhost', '127.0.0.1']:
        logger.warning("❌ MySQL configured for localhost (won't work in Replit)")
        logger.info("🔄 App will use PostgreSQL as fallback")
        logger.info("✅ Your WMS will work, but data goes to PostgreSQL")
    elif mysql_host and mysql_user and mysql_password and mysql_database:
        logger.info("✅ MySQL configured for external server")
        logger.info("🚀 Ready to test MySQL connection")
    else:
        logger.info("ℹ️ MySQL not fully configured")
        logger.info("🔄 App will use PostgreSQL")
    
    logger.info("\n💡 Next Steps:")
    if mysql_host and mysql_host.lower() in ['localhost', '127.0.0.1']:
        logger.info("1. Update MYSQL_HOST to external server address")
        logger.info("2. Or continue using PostgreSQL (recommended for Replit)")
    else:
        logger.info("1. Run: python mysql_complete_migration.py")
        logger.info("2. Test your WMS application")

if __name__ == "__main__":
    check_config()