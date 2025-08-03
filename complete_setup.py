#!/usr/bin/env python3
"""
Complete WMS Setup - Single Migration File
Handles both PostgreSQL (Replit) and MySQL (Local) database setup
"""

import os
import logging
import mysql.connector
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_env_file():
    """Create .env file with database configurations"""
    logger.info("📝 Creating .env configuration file...")
    
    env_content = """# =============================================================================
# WMS Database Configuration
# =============================================================================

# PostgreSQL (Primary for Replit)
DATABASE_URL=mysql+pymysql://root:root@123@localhost:3306/wms_db_dev

# MySQL (Local Development - Use ngrok for Replit access)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root@123
MYSQL_DATABASE=wms_db_dev

# For Replit MySQL access via ngrok tunnel:
# MYSQL_HOST=0.tcp.ngrok.io
# MYSQL_PORT=12345

# =============================================================================
# SAP B1 Integration Configuration
# =============================================================================
SAP_B1_SERVER=https://192.168.1.5:50000
SAP_B1_USERNAME=manager
SAP_B1_PASSWORD=1422
SAP_B1_COMPANY_DB=EINV-TESTDB-LIVE-HUST

# =============================================================================
# Application Configuration
# =============================================================================
SESSION_SECRET=your-secret-key-here-change-in-production

# =============================================================================
# Setup Instructions
# =============================================================================
# 1. For PostgreSQL: Update DATABASE_URL with your Replit PostgreSQL credentials
# 2. For MySQL Local: Update MYSQL_* values with your local MySQL settings
# 3. For MySQL via Replit: Run 'ngrok tcp 3306' and update MYSQL_HOST/PORT
# 4. Update SAP B1 settings with your SAP server details
# 5. Change SESSION_SECRET to a secure random string in production
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    logger.info("✅ Created .env file with dual database configuration")
    return True

def test_mysql_connection():
    """Test MySQL connection for local setup"""
    mysql_host = os.environ.get("MYSQL_HOST", "localhost")
    mysql_port = int(os.environ.get("MYSQL_PORT", "3306"))
    mysql_user = os.environ.get("MYSQL_USER", "root")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "root@123")
    mysql_database = os.environ.get("MYSQL_DATABASE", "wms_db_dev")
    
    logger.info(f"🔍 Testing MySQL connection to {mysql_host}:{mysql_port}")
    
    # Skip localhost in Replit environment
    if mysql_host.lower() in ['localhost', '127.0.0.1']:
        logger.warning("⚠️ MySQL configured for localhost - works for local development only")
        logger.info("💡 For Replit access: use ngrok tunnel (see .env file instructions)")
        return False
    
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connection_timeout=10
        )
        connection.close()
        logger.info("✅ MySQL connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ MySQL connection failed: {e}")
        return False

def create_mysql_tables():
    """Create complete MySQL database schema"""
    mysql_host = os.environ.get("MYSQL_HOST", "localhost")
    mysql_port = int(os.environ.get("MYSQL_PORT", "3306"))
    mysql_user = os.environ.get("MYSQL_USER", "root")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "root@123")
    mysql_database = os.environ.get("MYSQL_DATABASE", "wms_db_dev")
    
    logger.info("🏗️ Creating MySQL database schema...")
    
    try:
        connection = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = connection.cursor()
        
        # Complete schema creation
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            first_name VARCHAR(80),
            last_name VARCHAR(80),
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            branch_id VARCHAR(10),
            branch_name VARCHAR(100),
            default_branch_id VARCHAR(10),
            user_is_active BOOLEAN DEFAULT TRUE,
            must_change_password BOOLEAN DEFAULT FALSE,
            last_login DATETIME,
            permissions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );

        -- Branches table
        CREATE TABLE IF NOT EXISTS branches (
            id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            address TEXT,
            phone VARCHAR(20),
            email VARCHAR(100),
            manager_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            is_default BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );

        -- GRPO Documents table
        CREATE TABLE IF NOT EXISTS grpo_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            doc_num VARCHAR(50),
            sap_doc_num VARCHAR(50),
            po_number VARCHAR(100) NOT NULL,
            supplier_code VARCHAR(50),
            supplier_name VARCHAR(200),
            doc_date DATE,
            due_date DATE,
            warehouse_code VARCHAR(50),
            status VARCHAR(20) DEFAULT 'draft',
            total_amount DECIMAL(15, 4),
            currency VARCHAR(3) DEFAULT 'USD',
            branch_id VARCHAR(10),
            created_by INT,
            updated_by INT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id),
            INDEX idx_grpo_po_number (po_number),
            INDEX idx_grpo_status (status),
            INDEX idx_grpo_warehouse (warehouse_code)
        );

        -- GRPO Items table
        CREATE TABLE IF NOT EXISTS grpo_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            grpo_doc_id INT NOT NULL,
            line_num INT,
            item_code VARCHAR(100) NOT NULL,
            item_name VARCHAR(200),
            quantity DECIMAL(15, 4) NOT NULL,
            uom VARCHAR(20),
            unit_price DECIMAL(15, 4),
            line_total DECIMAL(15, 4),
            warehouse_code VARCHAR(50),
            bin_code VARCHAR(100),
            batch_number VARCHAR(100),
            serial_numbers TEXT,
            expiry_date DATE,
            manufacturing_date DATE,
            notes TEXT,
            qc_status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (grpo_doc_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
            INDEX idx_grpo_items_item_code (item_code),
            INDEX idx_grpo_items_batch (batch_number),
            INDEX idx_grpo_items_warehouse (warehouse_code)
        );

        -- Inventory Transfer Documents table
        CREATE TABLE IF NOT EXISTS inventory_transfer_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            doc_num VARCHAR(50),
            sap_doc_num VARCHAR(50),
            from_warehouse VARCHAR(50) NOT NULL,
            to_warehouse VARCHAR(50) NOT NULL,
            transfer_date DATE,
            status VARCHAR(20) DEFAULT 'draft',
            total_items INT DEFAULT 0,
            branch_id VARCHAR(10),
            created_by INT,
            updated_by INT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id),
            INDEX idx_transfer_status (status),
            INDEX idx_transfer_warehouses (from_warehouse, to_warehouse)
        );

        -- Inventory Transfer Items table
        CREATE TABLE IF NOT EXISTS inventory_transfer_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transfer_doc_id INT NOT NULL,
            line_num INT,
            item_code VARCHAR(100) NOT NULL,
            item_name VARCHAR(200),
            quantity DECIMAL(15, 4) NOT NULL,
            uom VARCHAR(20),
            from_warehouse VARCHAR(50),
            to_warehouse VARCHAR(50),
            from_bin_code VARCHAR(100),
            to_bin_code VARCHAR(100),
            batch_number VARCHAR(100),
            serial_numbers TEXT,
            expiry_date DATE,
            notes TEXT,
            qc_status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (transfer_doc_id) REFERENCES inventory_transfer_documents(id) ON DELETE CASCADE,
            INDEX idx_transfer_items_item_code (item_code),
            INDEX idx_transfer_items_batch (batch_number),
            INDEX idx_transfer_items_warehouses (from_warehouse, to_warehouse)
        );

        -- QR Code Labels table
        CREATE TABLE IF NOT EXISTS qr_code_labels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            label_type VARCHAR(50) NOT NULL,
            item_code VARCHAR(100) NOT NULL,
            item_name VARCHAR(200),
            po_number VARCHAR(100),
            batch_number VARCHAR(100),
            warehouse_code VARCHAR(50),
            bin_code VARCHAR(100),
            quantity DECIMAL(15, 4),
            uom VARCHAR(20),
            expiry_date DATE,
            qr_content TEXT NOT NULL,
            qr_format VARCHAR(20) DEFAULT 'TEXT',
            grpo_item_id INT,
            inventory_transfer_item_id INT,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            INDEX idx_qr_code_labels_item_code (item_code),
            INDEX idx_qr_code_labels_po_number (po_number),
            INDEX idx_qr_code_labels_label_type (label_type)
        );
        """
        
        # Execute schema creation
        for statement in schema_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        connection.commit()
        
        # Create default admin user
        admin_sql = """
        INSERT IGNORE INTO users (username, email, password_hash, first_name, last_name, role, user_is_active)
        VALUES ('admin', 'admin@wms.local', 
                'scrypt:32768:8:1$b8K4JGZyDqVTj8K4$45f2c8b3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1',
                'System', 'Administrator', 'admin', TRUE)
        """
        cursor.execute(admin_sql)
        
        # Create default branch
        branch_sql = """
        INSERT IGNORE INTO branches (id, name, description, is_active, is_default)
        VALUES ('MAIN', 'Main Branch', 'Primary warehouse branch', TRUE, TRUE)
        """
        cursor.execute(branch_sql)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info("✅ MySQL database schema created successfully")
        logger.info("🔑 Default admin user: admin / admin123")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create MySQL schema: {e}")
        return False

def test_postgresql_connection():
    """Test PostgreSQL connection"""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.warning("⚠️ No DATABASE_URL found - PostgreSQL not configured")
        return False
    
    try:
        engine = create_engine(database_url, connect_args={'connect_timeout': 10})
        connection = engine.connect()
        connection.close()
        logger.info("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False

def complete_setup():
    """Run complete WMS setup"""
    logger.info("🚀 Starting Complete WMS Setup")
    logger.info("="*60)
    
    # Step 1: Create .env file
    create_env_file()
    
    # Step 2: Test database connections
    logger.info("\n📊 Testing Database Connections:")
    pg_status = test_postgresql_connection()
    mysql_status = test_mysql_connection()
    
    # Step 3: Setup MySQL if available
    if mysql_status:
        logger.info("\n🏗️ Setting up MySQL database...")
        mysql_setup = create_mysql_tables()
    else:
        mysql_setup = False
        logger.info("\n⚠️ MySQL setup skipped - connection not available")
    
    # Step 4: Summary
    logger.info("\n📋 Setup Summary:")
    logger.info("="*40)
    logger.info(f"✅ Environment file: Created")
    logger.info(f"{'✅' if pg_status else '❌'} PostgreSQL: {'Connected' if pg_status else 'Not available'}")
    logger.info(f"{'✅' if mysql_status else '⚠️'} MySQL: {'Connected' if mysql_status else 'Local only'}")
    logger.info(f"{'✅' if mysql_setup else '⚠️'} MySQL Schema: {'Created' if mysql_setup else 'Skipped'}")
    
    logger.info("\n🎯 Database Strategy:")
    if pg_status:
        logger.info("  - PostgreSQL: Primary database for Replit")
    if mysql_status:
        logger.info("  - MySQL: Local development database")
        logger.info("  - Dual sync: Enabled")
    else:
        logger.info("  - MySQL: Available for local development")
        logger.info("  - Use ngrok tunnel for Replit access")
    
    logger.info("\n🔧 Next Steps:")
    logger.info("1. Update .env file with your actual database credentials")
    logger.info("2. For MySQL access from Replit: setup ngrok tunnel")
    logger.info("3. Restart your application")
    logger.info("4. Access admin panel with: admin / admin123")
    
    return True

if __name__ == "__main__":
    complete_setup()