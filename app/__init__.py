from flask import Flask
from flask_login import LoginManager
from config import config
from app.models import db, User
import os


def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.inventory import inventory_bp
    from app.routes.sales import sales_bp
    from app.routes.purchases import purchases_bp
    from app.routes.customers import customers_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.doctors import doctors_bp
    from app.routes.accounting import accounting_bp
    from app.routes.reports import reports_bp
    from app.routes.alerts import alerts_bp
    from app.routes.master import master_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(accounting_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(master_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app, login_manager
