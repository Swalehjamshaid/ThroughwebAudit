# /app/scheduler.py (Place this in the root /app directory, NOT /app/app)
import sys
import os
from datetime import datetime
from redis import Redis
from rq_scheduler import Scheduler

# Fix Python path for importing config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app.config import Config
from app.worker import start_audit_job 

def main():
    print(f"[{datetime.utcnow()}] Scheduler initializing...")
    
    redis_conn = Redis.from_url(Config.REDIS_URL)
    scheduler = Scheduler(connection=redis_conn, queue_name=Config.RQ_QUEUE_NAME)
    
    # Clear old jobs
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    # Schedule a recurring job (Example: Daily audit)
    scheduler.schedule(
        scheduled_at=datetime.utcnow(),
        func=start_audit_job,
        args=('https://my-company-main-site.com/', 1), 
        interval=86400, # Run every 24 hours
        repeat=None
    )
    
    print(f"[{datetime.utcnow()}] Daily audit task scheduled successfully.")

if __name__ == '__main__':
    main()
