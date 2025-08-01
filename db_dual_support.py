"""
Dual Database Support for WMS - Replit + MySQL Integration
This module provides dual database write functionality to maintain MySQL consistency
while running on Replit's SQLite environment.
"""

import os
import logging
from contextlib import contextmanager
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class DualDatabaseManager:
    """Manages dual writes to both SQLite (Replit) and MySQL (original) databases"""
    
    def __init__(self, app=None):
        self.mysql_engine = None
        self.mysql_session_factory = None
        self.app = app
        self.mysql_enabled = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self._setup_mysql_connection()
    
    def _setup_mysql_connection(self):
        """Setup MySQL connection using environment variables"""
        try:
            mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
            mysql_user = os.environ.get('MYSQL_USER', 'root')
            mysql_password = os.environ.get('MYSQL_PASSWORD', '')
            mysql_database = os.environ.get('MYSQL_DATABASE', 'wms_db_dev')
            mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
            
            if mysql_host and mysql_user and mysql_database:
                mysql_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
                
                self.mysql_engine = create_engine(
                    mysql_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False  # Set to True for SQL debugging
                )
                
                # Test connection
                with self.mysql_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                self.mysql_session_factory = sessionmaker(bind=self.mysql_engine)
                self.mysql_enabled = True
                
                logging.info("✅ MySQL dual database support enabled")
                
        except Exception as e:
            logging.warning(f"⚠️ MySQL dual database support disabled: {e}")
            self.mysql_enabled = False
    
    @contextmanager
    def mysql_session(self):
        """Context manager for MySQL database sessions"""
        if not self.mysql_enabled:
            yield None
            return
            
        session = self.mysql_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"MySQL session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_mysql_query(self, query, params=None):
        """Execute a raw MySQL query"""
        if not self.mysql_enabled:
            return None
            
        try:
            with self.mysql_engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                conn.commit()
                return result
        except Exception as e:
            logging.error(f"MySQL query execution failed: {e}")
            return None
    
    def sync_record_to_mysql(self, table_name, record_data, operation='insert'):
        """Sync a single record to MySQL database"""
        if not self.mysql_enabled:
            return False
            
        try:
            if operation == 'insert':
                columns = ', '.join(record_data.keys())
                placeholders = ', '.join([f':{key}' for key in record_data.keys()])
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                
            elif operation == 'update':
                set_clause = ', '.join([f"{key} = :{key}" for key in record_data.keys() if key != 'id'])
                query = f"UPDATE {table_name} SET {set_clause} WHERE id = :id"
                
            elif operation == 'delete':
                query = f"DELETE FROM {table_name} WHERE id = :id"
                
            result = self.execute_mysql_query(query, record_data)
            return result is not None
            
        except Exception as e:
            logging.error(f"Failed to sync {operation} to MySQL for table {table_name}: {e}")
            return False
    
    def bulk_sync_to_mysql(self, table_name, records, operation='insert'):
        """Bulk sync multiple records to MySQL"""
        if not self.mysql_enabled or not records:
            return False
            
        success_count = 0
        for record in records:
            if self.sync_record_to_mysql(table_name, record, operation):
                success_count += 1
                
        logging.info(f"✅ Synced {success_count}/{len(records)} records to MySQL table {table_name}")
        return success_count == len(records)

# Global instance
dual_db = DualDatabaseManager()

def init_dual_database(app):
    """Initialize dual database support with Flask app"""
    dual_db.init_app(app)
    return dual_db