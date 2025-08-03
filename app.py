import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("Environment variables loaded from .env file")
except ImportError:
    logging.info("python-dotenv not installed, using system environment variables")
except Exception as e:
    logging.warning(f"Could not load .env file: {e}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get(
    "SESSION_SECRET") or "dev-secret-key-change-in-production"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database - Priority: MySQL > PostgreSQL > SQLite
mysql_host = os.environ.get("MYSQL_HOST")
mysql_port = os.environ.get("MYSQL_PORT", "3306")
mysql_user = os.environ.get("MYSQL_USER") 
mysql_password = os.environ.get("MYSQL_PASSWORD")
mysql_database = os.environ.get("MYSQL_DATABASE")
database_url = os.environ.get("DATABASE_URL")

# Check if MySQL credentials are available (highest priority)
if mysql_host and mysql_user and mysql_password and mysql_database:
    try:
        # URL encode the password to handle special characters
        from urllib.parse import quote_plus
        encoded_password = quote_plus(mysql_password)
        
        # Check if running in Replit or local environment
        # LOCAL_DEVELOPMENT=true forces local mode
        force_local = os.environ.get('LOCAL_DEVELOPMENT', '').lower() == 'true'
        is_replit = not force_local and (os.environ.get('REPLIT_DEPLOYMENT_DOMAIN'))
        
        # Handle localhost case - only block in Replit environment
        if mysql_host.lower() in ['localhost', '127.0.0.1']:
            if is_replit:
                logging.error(f"❌ MySQL host '{mysql_host}' won't work in Replit cloud environment")
                logging.info("🔧 SOLUTION: Use ngrok to tunnel your local MySQL to Replit")
                logging.info("⏭️ Falling back to PostgreSQL until MySQL tunnel is configured")
                mysql_host = None  # Force fallback
            else:
                logging.info(f"✅ Local development detected - connecting to MySQL localhost")
        
        if mysql_host:  # Only if MySQL host is still valid (not None)
            mysql_url = f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_database}"
            logging.info(f"✅ Attempting MySQL connection: {mysql_host}/{mysql_database}")
            
            # Test the connection before setting it
            from sqlalchemy import create_engine
            test_engine = create_engine(mysql_url, connect_args={'connect_timeout': 10})
            test_connection = test_engine.connect()
            test_connection.close()
            
            app.config["SQLALCHEMY_DATABASE_URI"] = mysql_url
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
                "pool_recycle": 300,
                "pool_pre_ping": True,
                "pool_size": 10,
                "max_overflow": 20,
                "connect_args": {'connect_timeout': 10}
            }
            db_type = "mysql"
            logging.info(f"✅ MySQL connection successful: {mysql_host}/{mysql_database}")
    except Exception as e:
        logging.error(f"❌ MySQL connection failed: {e}")
        logging.info("🔧 Falling back to PostgreSQL/SQLite")
        mysql_host = None  # Force fallback
# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'

# SAP B1 Configuration
app.config['SAP_B1_SERVER'] = os.environ.get('SAP_B1_SERVER',
                                             'https://192.168.1.5:50000')
app.config['SAP_B1_USERNAME'] = os.environ.get('SAP_B1_USERNAME', 'manager')
app.config['SAP_B1_PASSWORD'] = os.environ.get('SAP_B1_PASSWORD', '1422')
app.config['SAP_B1_COMPANY_DB'] = os.environ.get('SAP_B1_COMPANY_DB',
                                                 'EINV-TESTDB-LIVE-HUST')

with app.app_context():
    # Import models to create tables
    import models
    import models_extensions
    
    # Initialize dual database support
    from db_dual_support import init_dual_database
    dual_db = init_dual_database(app)
    logging.info("🔄 Dual database support initialized")
    
    # Import api_batch_management later to avoid circular imports
# import api_batch_management
    db.create_all()
    logging.info("Database tables created")
    
    # Create default data for PostgreSQL database
    try:
        from models_extensions import Branch
        from werkzeug.security import generate_password_hash
        from models import User
        
        # Create default branch
        default_branch = Branch.query.filter_by(id='BR001').first()
        if not default_branch:
            default_branch = Branch()
            default_branch.id = 'BR001'
            default_branch.name = 'Main Branch'
            default_branch.description = 'Main Office Branch'
            default_branch.address = 'Main Office'
            default_branch.phone = '123-456-7890'
            default_branch.email = 'main@company.com'
            default_branch.manager_name = 'Branch Manager'
            default_branch.is_active = True
            default_branch.is_default = True
            db.session.add(default_branch)
            logging.info("Default branch created")
        
        # Create default admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@company.com'
            admin.password_hash = generate_password_hash('admin123')
            admin.first_name = 'System'
            admin.last_name = 'Administrator'
            admin.role = 'admin'
            admin.branch_id = 'BR001'
            admin.branch_name = 'Main Branch'
            admin.default_branch_id = 'BR001'
            admin.user_is_active = True
            admin.must_change_password = False
            db.session.add(admin)
            logging.info("Default admin user created")
            
        db.session.commit()
        logging.info("✅ Default data initialization completed")
        
    except Exception as e:
        logging.error(f"Error initializing default data: {e}")
        db.session.rollback()
        # Continue with application startup

# Initialize dual database support for MySQL sync
try:
    from db_dual_support import init_dual_database
    dual_db = init_dual_database(app)
    app.config['DUAL_DB'] = dual_db
    logging.info("✅ Dual database support initialized")
except Exception as e:
    logging.warning(f"⚠️ Dual database support not available: {e}")
    app.config['DUAL_DB'] = None

# Import routes to register them
import routes
