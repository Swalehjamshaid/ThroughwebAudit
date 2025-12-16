# /app/app/models.py
from datetime import datetime
from sqlalchemy.orm import relationship
import json
from flask_login import UserMixin 

# FIX: Use the resilient relative import. app.py loads this safely.
from .app import db 

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    reports = relationship('AuditReport', backref='auditor', lazy=True)

class AuditReport(db.Model):
    __tablename__ = 'audit_reports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    website_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    overall_score = db.Column(db.Float, default=0.0)
    metrics_json = db.Column(db.Text, nullable=False)
