# /app/worker.py (Place this in the root /app directory, NOT /app/app)
import os
import json
import logging
from redis import Redis
from rq import Worker, Connection
# Import the app factory and components using the absolute path
from app.app.app import create_app, db
from app.app.config import Config 
from app.app.models import AuditReport
from app.app.audit_service import AuditService

# Create the application instance 
app = create_app(os.getenv('FLASK_ENV', 'default')) 
redis_url = Config.REDIS_URL
queue_name = Config.RQ_QUEUE_NAME 
conn = Redis.from_url(redis_url)

def start_audit_job(url: str, user_id: int):
    """Main job function enqueued by the web app to perform the audit."""
    with app.app_context():
        app.logger.info(f"Starting audit for {url} by user {user_id}")
        
        # 1. Run the comprehensive audit
        results = AuditService.run_audit(url)
        
        # 2. Save results to Database
        report = AuditReport(
            user_id=user_id,
            website_url=url,
            overall_score=results['scores'].get('overall_score', 0.0),
            metrics_json=json.dumps(results)
        )
        db.session.add(report)
        db.session.commit()
        app.logger.info(f"Audit completed and report {report.id} saved.")

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(
            [queue_name], 
            connection=conn, 
            default_timeout=Config.MAX_AUDIT_TIMEOUT
        )
        worker.work(logging=True)
