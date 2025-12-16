# /app/app/core.py
import json
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file, current_app
from flask_login import login_required, current_user

# Import extensions and models defined in your app.py
from .app import db, requires_admin # Import the requires_admin decorator for consistency
from .models import User, AuditReport
# from .worker import start_audit_job # Assuming worker.py is in the same directory

# Create the core blueprint
core = Blueprint('core', __name__, template_folder='templates')

# --- Core Dashboard Templates (Post Login) ---
    
@core.route('/dashboard')
@login_required
def dashboard():
    reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.created_at.desc()).limit(10).all()
    return render_template('dashboard.html', reports=reports, is_public_page=False)
        
@core.route('/websites', methods=['GET', 'POST'])
@login_required
def websites():
    reports = AuditReport.query.filter_by(user_id=current_user.id).all()
    return render_template('websites.html', reports=reports, is_public_page=False)

@core.route('/audit', methods=['POST'])
@login_required
def audit():
    url = request.form.get('url')
    if not url:
        flash('URL is required to start an audit.', 'danger')
        return redirect(url_for('core.dashboard'))
        
    # Enqueue the audit job to the worker process (requires proper setup)
    # current_app.task_queue.enqueue(start_audit_job, url, current_user.id)
    
    flash(f'Audit initiated for {url}. Results will be ready shortly!', 'info')
    return redirect(url_for('core.dashboard'))

# --- Audit-Specific Dashboard Templates (Dynamic Route) ---
    
@core.route('/reports/<int:report_id>/summary')
@login_required
def report_detail(report_id):
    report = AuditReport.query.get_or_404(report_id)
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)
            
    return render_template('audit-summary.html', report=report, data=json.loads(report.metrics_json), is_public_page=False)

@core.route('/reports/<int:report_id>/view/<category_key>')
@login_required
def audit_category_view(report_id, category_key):
    report = AuditReport.query.get_or_404(report_id)
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    template_map = {
        'technical': 'audit-technical.html', 
        'seo': 'audit-seo.html', 
        'content': 'audit-content.html',
        'ux': 'audit-ux.html',
        'performance': 'audit-performance.html',
        'security': 'audit-security.html',
        'compliance': 'audit-compliance.html'
    }
        
    template_name = template_map.get(category_key)
    if not template_name:
        flash(f"Audit category '{category_key}' not found.", 'danger')
        return redirect(url_for('core.report_detail', report_id=report_id))

    return render_template(template_name, report=report, data=json.loads(report.metrics_json), category=category_key, is_public_page=False)


# --- Reports & Notifications Routes ---
    
@core.route('/reports')
@login_required
def reports():
    user_reports = AuditReport.query.filter_by(user_id=current_user.id).order_by(AuditReport.created_at.desc()).all()
    return render_template('reports.html', reports=user_reports, is_public_page=False)

@core.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if request.method == 'POST':
        # Placeholder for saving notification settings
        flash('Notification and schedule settings updated.', 'success')
        return redirect(url_for('core.notifications'))
    return render_template('notifications.html', is_public_page=False)

@core.route('/reports/<int:report_id>/download/pdf')
@login_required
def download_pdf(report_id):
    report = AuditReport.query.get_or_404(report_id)
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    # --- MOCK PDF GENERATION START ---
    # NOTE: You need to install 'weasyprint' for this to work.
    try:
        from weasyprint import HTML 
        html_string = render_template('report_pdf.html', report=report, data=json.loads(report.metrics_json))
        pdf_bytes = HTML(string=html_string).write_pdf()
    except ImportError:
        pdf_bytes = b"PDF Generation Library (WeasyPrint) is not installed."
        current_app.logger.error("WeasyPrint is not installed. PDF generation failed.")
        flash("PDF generation failed. The server is missing a required library.", 'danger')
        abort(500)
    # --- MOCK PDF GENERATION END ---
        
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'audit_report_{report.id}_{report.website_url.replace("http://", "").replace("https://", "")}.pdf'
    )
