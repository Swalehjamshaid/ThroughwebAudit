# Procfile

# The web process for Gunicorn
web: gunicorn app.app.app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 300

# The worker process for background tasks (PDF generation, emails)
worker: rq worker audit_tasks

# The scheduler process for recurring tasks (daily/weekly reports)
scheduler: python app/scheduler.py
