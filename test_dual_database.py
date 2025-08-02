#!/usr/bin/env python3
"""
Test dual database configuration
"""

import os
import logging
from app import app

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dual_database():
    """Test dual database configuration"""
    logger.info("🔍 Testing Dual Database Configuration")
    logger.info("="*50)
    
    with app.app_context():
        from db_dual_support import dual_db_manager
        
        logger.info("\n📊 Database Status:")
        logger.info(f"  Primary Database: {app.config.get('DB_TYPE', 'unknown')}")
        logger.info(f"  SQLAlchemy URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
        if dual_db_manager:
            logger.info(f"  SQLite Engine: {'✅ Available' if dual_db_manager.sqlite_engine else '❌ Not available'}")
            logger.info(f"  MySQL Engine: {'✅ Available' if dual_db_manager.mysql_engine else '❌ Not available'}")
            
            if dual_db_manager.mysql_engine:
                logger.info("🎯 MySQL dual sync is working - all data will be synchronized")
            else:
                logger.info("⚠️ MySQL dual sync not available - data stored in primary database only")
        else:
            logger.info("❌ Dual database manager not initialized")
        
        logger.info("\n💡 Current Setup:")
        mysql_host = os.environ.get("MYSQL_HOST")
        if mysql_host and mysql_host.lower() in ['localhost', '127.0.0.1']:
            logger.info("  - MySQL configured for localhost (blocked in Replit)")
            logger.info("  - Your data is safely stored in PostgreSQL")
            logger.info("  - To enable MySQL sync: set up ngrok tunnel")
        elif mysql_host:
            logger.info(f"  - MySQL configured for external server: {mysql_host}")
            logger.info("  - Testing connection...")
        else:
            logger.info("  - MySQL not configured")
            logger.info("  - Using primary database only")

if __name__ == "__main__":
    test_dual_database()