# /app/app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    
    # --- Database Config (Auto Connection) ---
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///audit.db")

    # CRITICAL FIX for Railway PostgreSQL Connection
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres"):
        # 1. Replace deprecated 'postgres://' with 'postgresql://' (SQLAlchemy requirement)
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
        # 2. Add required SSL mode for Railway proxy connections
        if "sslmode=" not in SQLALCHEMY_DATABASE_URI:
             SQLALCHEMY_DATABASE_URI += "?sslmode=require" if "?" not in SQLALCHEMY_DATABASE_URI else "&sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 600, 'max_overflow': 10}
    
    # Task Queue/Worker Config
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RQ_QUEUE_NAME = "audit_tasks"
    MAX_AUDIT_TIMEOUT = 300 
    
    # Email Config 
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', 'on', '1')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'user@example.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_email_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@webaudit.com')


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
