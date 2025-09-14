import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy_lite import SQLAlchemy
from flask_alembic import Alembic
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect

from extensions import Model, db, alembic, login_manager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    # Create the app
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # CSRF Protection
    csrf = CSRFProtect(app)

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///loyalty.db")
    app.config["SQLALCHEMY_ENGINES"] = {
        "default": app.config["SQLALCHEMY_DATABASE_URI"],
    }
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL query logging for debugging
    
    # Initialize extensions
    db.init_app(app)
    alembic.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from auth import auth_bp
    from dashboard import dashboard_bp
    from transactions import transactions_bp
    from map import map_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(map_bp)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return db.session.get(User, int(user_id))
    
    # Home route
    @app.route('/')
    def index():
        from flask import render_template
        from flask_login import current_user
        return render_template('index.html', user=current_user)

    # Error handler for 404 Not Found
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    return app
