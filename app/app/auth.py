# /app/app/auth.py

# Note: You MUST import the necessary components from your main application's scope
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from sqlalchemy import exc

# Import extensions and models defined in your app.py
from .app import db, bcrypt, mail
from .models import User 
from .utils import send_verification_email # Assume this utility is in a separate utils.py

# Create the auth blueprint
auth = Blueprint('auth', __name__, template_folder='templates')

# --- Authentication & User Management Routes ---

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
            
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
            if not user.is_verified:
                flash('Account not verified. Please check your email.', 'warning')
                return redirect(url_for('auth.login'))
            login_user(user, remember=True)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('core.dashboard'))
        else:
            flash('Login failed. Check email and password.', 'danger')
            
    return render_template('login.html', is_public_page=True)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
            
    if request.method == 'POST':
        if User.query.filter_by(email=request.form.get('email')).first():
            flash('Email address is already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        new_user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            password_hash=hashed_password,
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()
        # send_verification_email(new_user) # Uncomment and implement this function properly
        flash('Registration successful! Please check your email for a verification link.', 'info')
        return redirect(url_for('auth.login'))
            
    return render_template('register.html', is_public_page=True)
    
@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('marketing.index'))

@auth.route('/verify/<token>')
def verify_email(token):
    # This entire block needs proper implementation using a secure token method (e.g., Flask-Mail/ItsDangerous)
    # Mocking user retrieval for now
    user = User.query.filter_by(id=1).first() 
    success = (token.startswith("temp_verification_token"))
    if success and user:
        user.is_verified = True
        db.session.commit()
        flash('Email verified successfully!', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('verify-email.html', success=success, message='Invalid or expired verification link.', can_resend=not success, email=user.email if user else '')

@auth.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html', is_public_page=True)

@auth.route('/reset-password/<token>')
def reset_password(token):
    return render_template('reset-password.html', is_public_page=True, token=token)
