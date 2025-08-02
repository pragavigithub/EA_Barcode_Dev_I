#!/usr/bin/env python3
"""
MySQL Complete Migration Script for WMS
Handles database migration and ensures data goes to MySQL database
"""

import os
import logging
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("Environment variables loaded from .env file")
except ImportError:
    logging.warning("python-dotenv not installed, using system environment variables")
except Exception as e:
    logging.warning(f"Could not load .env file: {e}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_mysql_connection():
    """Test MySQL connection with current credentials"""
    mysql_host = os.environ.get("MYSQL_HOST")
    mysql_port = os.environ.get("MYSQL_PORT", "3306")
    mysql_user = os.environ.get("MYSQL_USER") 
    mysql_password = os.environ.get("MYSQL_PASSWORD")
    mysql_database = os.environ.get("MYSQL_DATABASE")
    
    logger.info(f"Current MySQL Config:")
    logger.info(f"  Host: {mysql_host}")
    logger.info(f"  User: {mysql_user}")
    logger.info(f"  Database: {mysql_database}")
    logger.info(f"  Password: {'*' * len(mysql_password) if mysql_password else 'None'}")
    
    if not all([mysql_host, mysql_user, mysql_password, mysql_database]):
        logger.error("❌ Missing MySQL credentials")
        logger.info("Required: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE")
        return False
    
    # Check if localhost is being used
    if mysql_host.lower() in ['localhost', '127.0.0.1']:
        logger.error("❌ MySQL host is 'localhost' - this won't work in Replit")
        logger.info("💡 You need to provide an external MySQL server address")
        logger.info("")
        logger.info("📋 To fix this, update your Replit Secrets or .env file:")
        logger.info("  MYSQL_HOST=your-external-mysql-server.com")
        logger.info("")
        logger.info("Examples of external MySQL hosts:")
        logger.info("  - your-domain.com")
        logger.info("  - db.your-hosting-provider.com")
        logger.info("  - mysql.your-website.com")
        logger.info("  - External IP like 203.0.113.10 (if accessible from internet)")
        logger.info("")
        logger.info("🔧 Alternative Solutions:")
        logger.info("  1. Use ngrok to expose your local MySQL:")
        logger.info("     - Run: ngrok tcp 3306")
        logger.info("     - Update MYSQL_HOST to ngrok URL")
        logger.info("  2. Use PostgreSQL (already working)")
        logger.info("     - Your app automatically uses PostgreSQL")
        logger.info("     - All data stored safely")
        logger.info("")
        logger.info("💡 Run: python setup_local_mysql_tunnel.py for detailed guide")
        return False
    
    try:
        # URL encode password to handle special characters
        encoded_password = quote_plus(mysql_password)
        mysql_url = f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        
        logger.info(f"🔍 Testing MySQL connection to {mysql_host}/{mysql_database}")
        
        # Create test engine with timeout
        engine = create_engine(mysql_url, connect_args={'connect_timeout': 10})
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                logger.info("✅ MySQL connection successful!")
                
                # Test database info
                db_info = connection.execute(text("SELECT DATABASE(), USER(), VERSION()"))
                db_name, user, version = db_info.fetchone()
                logger.info(f"📊 Connected to: {db_name} as {user} (MySQL {version})")
                return True
            else:
                logger.error("❌ MySQL test query failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ MySQL connection failed: {str(e)}")
        logger.info("💡 Common issues:")
        logger.info("  - MySQL server not accessible from internet")
        logger.info("  - Firewall blocking connection")
        logger.info("  - Wrong host/port/credentials")
        logger.info("  - MySQL server not running")
        return False

def create_mysql_tables():
    """Create WMS tables in MySQL database"""
    from app import app, db
    
    with app.app_context():
        try:
            # Import all models to ensure tables are created
            import models
            import models_extensions
            
            logger.info("📝 Creating MySQL tables...")
            db.create_all()
            logger.info("✅ MySQL tables created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create MySQL tables: {e}")
            return False

def migrate_to_mysql():
    """Complete migration to MySQL database"""
    logger.info("🚀 Starting MySQL migration...")
    
    if test_mysql_connection():
        logger.info("✅ MySQL connection verified - proceeding with migration")
        
        if create_mysql_tables():
            logger.info("✅ MySQL migration completed successfully!")
            logger.info("📊 Your WMS data will now be stored in MySQL database")
            return True
        else:
            logger.error("❌ MySQL table creation failed")
            return False
    else:
        logger.error("❌ MySQL connection failed - migration aborted")
        logger.info("🔧 Currently using PostgreSQL as fallback")
        return False

if __name__ == "__main__":
    migrate_to_mysql()