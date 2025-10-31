from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables FIRST
load_dotenv()

# Import blueprints
from assets_discovery.backend import assets_discovery_bp
from crlf.backend import crlf_bp
from filefetcher.backend import filefetcher_bp
from js.backend import js_bp
from lfi.backend import lfi_bp  # Fixed from "ilf"
from open_redirect.backend import open_redirect_bp
from passive.backend import passive_bp
from port.backend import port_bp
from sql_injection.backend import sql_injection_bp
from ssl_scanner.backend import ssl_bp
from ssti.backend import ssti_bp
from subdomain_finder.app import subdomain_finder_bp
from tech.backend import tech_bp
from xss.backend import xss_bp
from lina_chatbot.backend import lina_bp  # NEW: Import LINA chatbot
from reports.backend import reports_bp

# Flask will automatically use 'templates' folder by default
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', "jashanth@123")
CORS(app)

# Register Blueprints
app.register_blueprint(assets_discovery_bp, url_prefix='/api/assets-discovery')
app.register_blueprint(crlf_bp, url_prefix='/api/crlf')
app.register_blueprint(filefetcher_bp, url_prefix='/api/filefetcher')
app.register_blueprint(js_bp, url_prefix='/api/js')
app.register_blueprint(lfi_bp, url_prefix='/api/lfi')
app.register_blueprint(open_redirect_bp, url_prefix='/api/open-redirect')
app.register_blueprint(passive_bp, url_prefix='/api/passive-links')
app.register_blueprint(port_bp, url_prefix='/api/port-scan')
app.register_blueprint(sql_injection_bp, url_prefix='/api/sqli')
app.register_blueprint(ssl_bp, url_prefix='/api/tls-test')
app.register_blueprint(ssti_bp, url_prefix='/api/ssti-test')
app.register_blueprint(subdomain_finder_bp, url_prefix='/api/subdomains')
app.register_blueprint(tech_bp, url_prefix='/api/tech-detect')
app.register_blueprint(xss_bp, url_prefix='/api/xss')
app.register_blueprint(lina_bp, url_prefix='/api/ask-lina')  # NEW: Register LINA chatbot
app.register_blueprint(reports_bp, url_prefix='/api/reports')


@app.route('/')
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'password':
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        error = "Invalid username or password"
        return render_template('index.html', error=error)


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    username = session.get('username', 'Admin')
    return render_template('dashboard.html', username=username)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/api/change-password', methods=['POST'])
def change_password():
    """Handle password change requests"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    username = session.get('username')
    
    # Validation
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    # Verify current password (hardcoded for demo - replace with database check in production)
    if username == 'admin' and current_password != 'password':
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 403
    
    # In production, you would:
    # 1. Hash the new password using bcrypt or similar
    # 2. Update it in your database
    # 3. Optionally force re-login
    # For now, we'll just return success (since this is a demo with hardcoded credentials)
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})


@app.route('/api/change-username', methods=['POST'])
def change_username():
    """Handle username change requests"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.json
    new_username = data.get('new_username', '').strip()
    
    # Validation
    if not new_username:
        return jsonify({'success': False, 'error': 'Username cannot be empty'}), 400
    
    if len(new_username) < 3:
        return jsonify({'success': False, 'error': 'Username must be at least 3 characters'}), 400
    
    if len(new_username) > 50:
        return jsonify({'success': False, 'error': 'Username must be less than 50 characters'}), 400
    
    # Update session
    session['username'] = new_username
    
    return jsonify({'success': True, 'message': 'Username updated successfully', 'username': new_username})


if __name__ == "__main__":
    print("=" * 50)
    print(" Starting LINA Security Scanner")
    print("=" * 50)
    
    # Check if Groq API key is set
    if os.getenv('GROQ_API_KEY'):
        print("✓ LINA_API_KEY found")
    else:
        print("⚠️  WARNING: LINA_API_KEY not found in .env file")
        print("   LINA chatbot will not work without it!")
        print("   Get free API key: https://console.groq.com/keys")
    
    print("📍 [LINA] is LIVE")
    print("📍 Server running at: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)