# /app/app/marketing.py
from flask import Blueprint, render_template

# Create the marketing blueprint
marketing = Blueprint('marketing', __name__, template_folder='templates')

# --- Public / Marketing Pages (Accessible without login) ---

@marketing.route('/')
def index():
    # Renders the homepage
    return render_template('index.html', is_public_page=True)

@marketing.route('/about')
def about():
    # Renders the about us page
    return render_template('about.html', is_public_page=True)

@marketing.route('/features')
def features():
    # Renders the features page
    return render_template('features.html', is_public_page=True)

@marketing.route('/pricing')
def pricing():
    # Renders the pricing page
    return render_template('pricing.html', is_public_page=True)
    
@marketing.route('/contact')
def contact():
    # Renders the contact page
    return render_template('contact.html', is_public_page=True)

@marketing.route('/maintenance')
def maintenance():
    # Renders the maintenance page
    return render_template('maintenance.html', is_public_page=True)
