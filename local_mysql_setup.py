#!/usr/bin/env python3
"""
Local MySQL Setup for WMS
Run this on your local machine to setup MySQL database
"""

import os
import sys
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_local_env():
    """Setup local environment for MySQL"""
    logger.info("🔧 Setting up local MySQL environment...")
    
    # Copy local config
    if os.path.exists('.env.local'):
        shutil.copy('.env.local', '.env')
        logger.info("✅ Copied .env.local to .env for local development")
    else:
        logger.error("❌ .env.local file not found")
        return False
    
    # Test the setup
    from app import app
    with app.app_context():
        try:
            from app import db, db_type
            logger.info(f"✅ Database type: {db_type}")
            
            # Test database connection
            db.create_all()
            logger.info("✅ Database tables created/verified")
            
            # Check dual database
            from db_dual_support import dual_db_manager
            if dual_db_manager and dual_db_manager.mysql_engine:
                logger.info("✅ MySQL dual database sync enabled")
            else:
                logger.info("ℹ️ MySQL dual sync not available (this is okay)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False

def main():
    """Main setup function"""
    logger.info("🚀 WMS Local MySQL Setup")
    logger.info("="*40)
    
    # Check if running on local machine
    if os.environ.get('REPLIT_DEPLOYMENT_DOMAIN'):
        logger.error("❌ This script is for local development only")
        logger.info("💡 Run this on your local machine, not in Replit")
        return False
    
    logger.info("💻 Local machine detected - proceeding with MySQL setup")
    
    if setup_local_env():
        logger.info("\n✅ Local MySQL setup completed successfully!")
        logger.info("📋 Next steps:")
        logger.info("  1. Start your local WMS application")
        logger.info("  2. Access: http://localhost:5000")
        logger.info("  3. Login with admin / admin123")
        return True
    else:
        logger.error("\n❌ Setup failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)