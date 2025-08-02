"""
Dual Database Support Module
Handles both SQLite (for Replit) and MySQL (for local development) synchronization
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import json
from datetime import datetime

class DualDatabaseManager:
    """Manages dual database support for SQLite and MySQL"""
    
    def __init__(self, app):
        self.app = app
        self.sqlite_engine = None
        self.mysql_engine = None
        self.setup_engines()
    
    def setup_engines(self):
        """Setup both SQLite and MySQL engines"""
        # SQLite engine (primary for Replit)
        sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'wms.db')
        self.sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        
        # MySQL engine (for local development sync)
        mysql_config = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': os.environ.get('MYSQL_PORT', '3306'),
            'user': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ.get('MYSQL_PASSWORD', 'root@123'),
            'database': os.environ.get('MYSQL_DATABASE', 'wms_db_dev')
        }
        
        # Check if running in Replit or local environment
        # LOCAL_DEVELOPMENT=true forces local mode
        force_local = os.environ.get('LOCAL_DEVELOPMENT', '').lower() == 'true'
        is_replit = not force_local and (os.environ.get('REPLIT_DEPLOYMENT_DOMAIN') or os.environ.get('REPLIT_DB_URL') or 'replit' in os.environ.get('HOSTNAME', '').lower())
        
        # Check if localhost MySQL (only block in Replit)
        if mysql_config['host'].lower() in ['localhost', '127.0.0.1']:
            if is_replit:
                logging.warning(f"⚠️ MySQL host '{mysql_config['host']}' detected in dual database - won't work in Replit")
                logging.info("💡 To enable MySQL sync: update MYSQL_HOST to external server or use ngrok tunnel")
                logging.info("🔄 Operating in SQLite-only mode")
                self.mysql_engine = None
                return
            else:
                logging.info(f"✅ Local development detected - enabling MySQL dual sync for localhost")
        
        try:
            from urllib.parse import quote_plus
            encoded_password = quote_plus(mysql_config['password'])
            mysql_url = f"mysql+pymysql://{mysql_config['user']}:{encoded_password}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
            
            # Test connection before creating engine
            test_engine = create_engine(mysql_url, connect_args={'connect_timeout': 5})
            test_connection = test_engine.connect()
            test_connection.close()
            
            self.mysql_engine = create_engine(mysql_url, connect_args={'connect_timeout': 10})
            logging.info(f"✅ MySQL dual database sync enabled: {mysql_config['host']}/{mysql_config['database']}")
        except Exception as e:
            logging.warning(f"⚠️ MySQL dual database setup failed: {e}")
            logging.info("🔄 Operating in SQLite-only mode")
            self.mysql_engine = None
    
    def sync_to_mysql(self, table_name, operation, data=None, where_clause=None):
        """Synchronize changes to MySQL database"""
        if not self.mysql_engine:
            logging.debug(f"MySQL dual sync not available for {table_name} - using primary database only")
            return
        
        if not data and operation in ['INSERT', 'UPDATE']:
            logging.warning(f"No data provided for {operation} operation on {table_name}")
            return
        
        try:
            with self.mysql_engine.connect() as conn:
                if operation == 'INSERT' and data:
                    # Build INSERT statement
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join([f":{key}" for key in data.keys()])
                    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    conn.execute(text(sql), data)
                    
                elif operation == 'UPDATE' and data:
                    # Build UPDATE statement
                    set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                    conn.execute(text(sql), data)
                    
                elif operation == 'DELETE':
                    # Build DELETE statement
                    sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                    conn.execute(text(sql), data or {})
                
                conn.commit()
                logging.debug(f"✅ Synced {operation} to MySQL: {table_name}")
                
        except SQLAlchemyError as e:
            logging.error(f"❌ MySQL sync failed for {table_name}: {e}")
        except Exception as e:
            logging.error(f"❌ Unexpected error during MySQL sync: {e}")
    
    def execute_dual_query(self, sql, params=None):
        """Execute query on both databases"""
        results = {'sqlite': [], 'mysql': []}
        
        # Execute on SQLite
        if self.sqlite_engine:
            try:
                with self.sqlite_engine.connect() as conn:
                    result = conn.execute(text(sql), params or {})
                    if result.returns_rows:
                        results['sqlite'] = result.fetchall()
                    else:
                        results['sqlite'] = result.rowcount
            except Exception as e:
                logging.error(f"SQLite query failed: {e}")
        
        # Execute on MySQL if available
        if self.mysql_engine:
            try:
                with self.mysql_engine.connect() as conn:
                    result = conn.execute(text(sql), params or {})
                    if result.returns_rows:
                        results['mysql'] = result.fetchall()
                    else:
                        results['mysql'] = result.rowcount
                    conn.commit()
            except Exception as e:
                logging.error(f"MySQL query failed: {e}")
        
        return results

# Global instance
dual_db_manager = None

def init_dual_database(app):
    """Initialize dual database support"""
    global dual_db_manager
    dual_db_manager = DualDatabaseManager(app)
    return dual_db_manager

def sync_model_change(model_name, operation, data, where_clause=None):
    """Helper function to sync model changes"""
    if dual_db_manager:
        # Convert SQLAlchemy model name to table name
        table_name = model_name.lower() + 's' if not model_name.endswith('s') else model_name.lower()
        dual_db_manager.sync_to_mysql(table_name, operation, data, where_clause)