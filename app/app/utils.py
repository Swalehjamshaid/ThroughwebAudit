# /app/app/utils.py

import os
from flask import url_for, current_app, flash
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer # Recommended for secure tokens

# Note: The 'User' model is imported within the functions below to avoid circular imports 
# if the model relies on the 'db' object initialized in app.py.

def generate_token(user, expiration=3600):
    """
    Generates a secure, time-limited token for email verification or password reset.
    """
    s = Serializer(current_app.config['SECRET_KEY'], salt='email-confirm')
    return s.dumps({'user_id': user.id})

def load_token(token, max_age=3600):
    """
    Loads and verifies a secure token, returning the user ID if valid.
    Returns None if the token is invalid or expired.
    """
    s = Serializer(current_app.config['SECRET_KEY'], salt='email-confirm')
    try:
        data = s.loads(token, max_age=max_age)
        return data['user_id']
    except Exception:
        return None

def send_verification_email(user):
    """
    Sends the account verification email to a new user.
    """
    token = generate_token(user)
    
    # Generate the verification link using the 'auth.verify_email' endpoint
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    msg = Message(
        'Verify Your Web Audit Account',
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=[user.email],
        body=f"""
Hello {user.username},

Thank you for registering with ThroughwebAudit!

Please click the link below to verify your account:
{verify_url}

If you did not request this, please ignore this email.

The ThroughwebAudit Team
"""
    )
    
    try:
        # Check if MAIL_SUPPRESS_SEND is true (often in testing)
        if current_app.config.get('MAIL_SUPPRESS_SEND'):
            current_app.logger.info(f"Mock verification email (SUPPRESSED) sent to {user.email}. Token: {token}")
            return True
            
        current_app.mail.send(msg)
        current_app.logger.info(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email to {user.email}: {e}")
        # Note: Flash message should ideally be handled in the calling route
        return False
