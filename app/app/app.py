# /app/app/app.py

import os
import click
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import exc
from rq import Queue
from redis import Redis
from datetime import datetime

# Import modules from the application package
from . import audit_service   
from .config import config_map
# Importing User model here is safe for LoginManager/type hints
from .models import User, AuditReport

# --- 1. Initialize Extensions Globally ---
db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
# Message category for unauthenticated users
login_manager.login_message_category = 'warning'
login_manager.login_message = 'Please log in to access this page.'


# --- 2. Database Model Loader Fix (Prevents Gunicorn Crash) ---
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

    # --- Utility Functions (Placeholders for security logic) ---
    def generate_token(user):
        """Placeholder for generating a secure verification token."""
        return "temp_verification_token_for_" + str(user.id)
    
    def send_verification_email(user):
        """Placeholder for sending the verification email."""
        token = generate_token(user)
        msg = Message('Verify Your Web Audit Account', 
                      recipients=[user.email], 
                      body=f'Click the link to verify your account: {url_for("verify_email", token=token, _external=True)}')
        try:
            mail.send(msg)
            app.logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")
            flash('Failed to send verification email. Check MAIL_ settings.', 'danger')

    # --- 3. Public / Marketing Pages (Accessible without login) ---

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/features')
    def features():
        return render_template('features.html')

    @app.route('/pricing')
    def pricing():
        return render_template('pricing.html')
        
    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    # --- 4. Authentication & User Management Templates ---
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            user = User.query.filter_by(email=request.form.get('email')).first()
            
            if user and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
                if not user.is_verified:
                    flash('Account not verified. Please check your email.', 'warning')
                    return redirect(url_for('login'))
                    
                login_user(user, remember=True)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Login failed. Check email and password.', 'danger')
        
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            # --- Dummy registration logic ---
            hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
            new_user = User(
                username=request.form.get('username'),
                email=request.form.get('email'),
                password_hash=hashed_password,
                is_verified=False # Must be verified via email
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Trigger email verification
            send_verification_email(new_user) 

            flash('Registration successful! Please check your email for a verification link.', 'info')
            return redirect(url_for('login'))
            
        return render_template('register.html')
        
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('index'))

    @app.route('/verify/<token>')
    def verify_email(token):
        # In a real app, token logic would happen here (e.g., JWT decode)
        user = User.query.filter_by(id=1).first() # Placeholder logic
        if user and token.startswith("temp_verification_token"):
            user.is_verified = True
            db.session.commit()
            return render_template('verify-email.html', success=True)
        return render_template('verify-email.html', success=False, message='Invalid or expired verification link.', can_resend=True, email=user.email if user else '')

    @app.route('/forgot-password')
    def forgot_password():
        return render_template('forgot-password.html')

    @app.route('/reset-password/<token>')
    def reset_password(token):
        return render_template('reset-password.html')

    # --- 5. Core Dashboard Templates (Post Login) ---
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.created_at.desc()).limit(10).all()
        # Renders the Main Dashboard
        return render_template('dashboard.html', reports=reports)
        
    @app.route('/websites')
    @login_required
    def websites():
        # Renders the Website Management Page
        reports = AuditReport.query.filter_by(user_id=current_user.id).all()
        return render_template('websites.html', reports=reports)


    # --- 6. Audit Execution and Reporting Routes ---
    
    @app.route('/audit', methods=['POST'])
    @login_required
    def audit():
        url = request.form.get('url')
        if not url:
            flash('URL is required to start an audit.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Enqueue the audit job to the worker process
        from .worker import start_audit_job 
        app.task_queue.enqueue(start_audit_job, url, current_user.id)
        
        flash(f'Audit initiated for {url}. Results will be ready shortly!', 'info')
        return redirect(url_for('dashboard'))

    @app.route('/reports/<int:report_id>')
    @login_required
    def report_detail(report_id):
        report = AuditReport.query.get_or_404(report_id)
        if report.user_id != current_user.id and not current_user.is_admin:
            flash("Access denied to this report.", 'danger')
            return redirect(url_for('dashboard'))
            
        # Renders the Executive Summary Page
        return render_template('audit-summary.html', report=report, data=json.loads(report.metrics_json))

    @app.route('/reports/<int:report_id>/download/pdf')
    @login_required
    def download_pdf(report_id):
        # NOTE: PDF Generation should be done by the worker, but this route serves it.
        # This route requires `weasyprint` and your full implementation in worker.py
        
        from .worker import generate_pdf_report # Assuming this function exists in worker.py
        report = AuditReport.query.get_or_404(report_id)
        
        # Placeholder for actual PDF generation logic (requires worker.py)
        # pdf_bytes = generate_pdf_report(report_id) 
        
        # For simplicity, we just redirect for now. Actual implementation would return send_file(pdf_bytes, ...)
        flash('PDF report is being generated and will be served shortly (functionality is mocked).', 'warning')
        return redirect(url_for('report_detail', report_id=report_id))
    
    @app.route('/reports')
    @login_required
    def reports():
        # Renders the Audit Reports Page
        user_reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.created_at.desc()).all()
        return render_template('reports.html', reports=user_reports)

    @app.route('/notifications')
    @login_required
    def notifications():
        # Renders the Email Schedule & Notifications Page
        return render_template('notifications.html')

    # --- 7. Audit-Specific Dashboard Templates (Simplified Placeholder Routes) ---
    
    @app.route('/audit/<int:report_id>/<category>')
    @login_required
    def audit_category_view(report_id, category):
        # Maps all category views (technical, seo, content, etc.) to one function
        report = AuditReport.query.get_or_404(report_id)
        if report.user_id != current_user.id and not current_user.is_admin:
            flash("Access denied to this report.", 'danger')
            return redirect(url_for('dashboard'))

        template_map = {
            'technical': 'audit-technical.html', 
            'seo': 'audit-seo.html', 
            'content': 'audit-content.html',
            'ux': 'audit-ux.html',
            'performance': 'audit-performance.html',
            'security': 'audit-security.html',
            'compliance': 'audit-compliance.html'
        }
        
        template_name = template_map.get(category)
        if not template_name:
            return redirect(url_for('report_detail', report_id=report_id))

        return render_template(template_name, report=report, data=json.loads(report.metrics_json), category=category)


    # --- 8. Admin-Specific Templates ---
    
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if not current_user.is_admin:
            return render_template('403.html'), 403 # Access Denied Page
        # Renders the Admin Dashboard
        return render_template('admin-dashboard.html')

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if not current_user.is_admin:
            return render_template('403.html'), 403 
        # Renders the User Management Page
        users = User.query.all()
        return render_template('admin-users.html', users=users)

    @app.route('/admin/settings')
    @login_required
    def admin_settings():
        if not current_user.is_admin:
            return render_template('403.html'), 403 
        # Renders the System Settings Page
        return render_template('admin-settings.html')

    # --- 9. Error & Utility Templates ---
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404 # Page Not Found

    @app.errorhandler(403)
    def access_denied(e):
        return render_template('403.html'), 403 # Access Denied

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500 # Server Error


    # Register CLI commands
    register_cli(app)

    return app

# --- 10. CLI Commands for Database Management (Auto Table Creation) ---
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
