# /app/app/admin.py
from flask import Blueprint, render_template, abort
from flask_login import login_required

# Import extensions and models defined in your app.py
from .app import requires_admin # Use the decorator from app.py
from .models import User

# Create the admin blueprint
admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')

# --- Admin-Specific Routes ---
    
@admin.route('/dashboard')
@login_required
@requires_admin
def admin_dashboard():
    return render_template('admin-dashboard.html', is_public_page=False)

@admin.route('/users')
@login_required
@requires_admin
def admin_users():
    users = User.query.all()
    return render_template('admin-users.html', users=users, is_public_page=False)

@admin.route('/audit-settings')
@login_required
@requires_admin
def admin_audit_settings():
    return render_template('admin-audit-settings.html', is_public_page=False)
        
@admin.route('/settings')
@login_required
@requires_admin
def admin_settings():
    return render_template('admin-settings.html', is_public_page=False)
