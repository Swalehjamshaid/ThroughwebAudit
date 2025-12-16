# /app/app/app.py

import os
import click
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import exc
from rq import Queue
from redis import Redis

# --- CRITICAL APPLICATION IMPORTS ---
from . import audit_service   
from .config import config_map
from .models import User 

# Initialize extensions globally
db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'

# Define a function to load models (PREVENTS GUNICORN CRASH)
def import_models():
    """Import models to ensure they are registered with SQLAlchemy."""
    from . import models 
    
def create_app(config_name=os.getenv('FLASK_ENV', 'default')):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_map.get(config_name, 'default')) 

    # Initialize extensions with the application instance
    db.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Configure RQ Queue (Auto Connection to Redis)
    app.redis_conn = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = Queue(app.config['RQ_QUEUE_NAME'], connection=app.redis_conn)

    # Load models now that 'db' is initialized with the app
    with app.app_context():
        import_models()
    
    # --- Login Manager User Loader ---
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Routes ---
    @app.route('/')
    @login_required
    def index():
        from .models import AuditReport
        reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.created_at.desc()).limit(10).all()
        return render_template('index.html', reports=reports)

    @app.route('/audit', methods=['POST'])
    @login_required
    def audit():
        url = request.form.get('url')
        if not url:
            return redirect(url_for('index'))
        
        from .worker import start_audit_job 
        app.task_queue.enqueue(start_audit_job, url, current_user.id)
        
        return redirect(url_for('index', message="Audit initiated! Check back shortly."))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # ... (login logic)
        return render_template('login.html')

    # Register CLI commands
    register_cli(app)

    return app

# --- CLI Commands for Database Management (Auto Table Creation) ---
def register_cli(app):
    @app.cli.group()
    def db_cli():
        """Database management commands (create, drop)."""
        pass

    @db_cli.command('create_all')
    @click.option('--drop-first', is_flag=True, help='Drop all tables first before creating.')
    def create_all_command(drop_first):
        print("Attempting to connect to database and create all tables...")
        with app.app_context():
            try:
                # CRITICAL: Ensures models are loaded before creating tables
                import_models() 
                if drop_first:
                    print("⚠️ Dropping existing tables...")
                    db.drop_all()
                
                db.create_all() 
                print("✅ Database tables created successfully.")
            except exc.OperationalError as e:
                print("❌ FAILED to connect to the database or create tables.")
                print("ACTION REQUIRED: Check your PostgreSQL server status and config.")
                exit(1)

# Entry point for Gunicorn
app = create_app()
