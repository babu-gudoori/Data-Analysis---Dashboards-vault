from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
from datetime import datetime
from markupsafe import Markup
from dotenv import load_dotenv
from collections import defaultdict
import json, os, re, uuid, time, secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

# Mail configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME")
)
mail = Mail(app)

DATA_FILE = "dashboards.json"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Track failed attempts
failed_attempts = defaultdict(int)
blocked_ips = {}
BLOCK_THRESHOLD = 5
BLOCK_TIME_SECONDS = 300  # 5 minutes

# ------------------ Utility Functions ------------------ #
def load_dashboards():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_dashboards(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def format_description(desc):
    if not desc:
        return ''
    desc = desc.replace('\n', '<br>')
    desc = re.sub(r'(#\w+)', r'<span class="hashtag">\1</span>', desc)
    return Markup(desc)

def generate_dashboard_id(title):
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    unique_id = str(uuid.uuid4())[:8]
    return f"{slug}-{unique_id}"

# ------------------ Secure Admin Shortcut ------------------ #
@app.route('/trigger_admin_shortcut')
def trigger_admin_shortcut():
    token = secrets.token_urlsafe(16)
    session['admin_token'] = token
    session['admin_token_time'] = int(time.time())
    return redirect(url_for('login_with_token', token=token))

@app.route('/login/<token>', methods=['GET', 'POST'])
def login_with_token(token):
    ip = request.remote_addr
    now = int(time.time())

    # Block if IP has been flagged
    if ip in blocked_ips and now - blocked_ips[ip] < BLOCK_TIME_SECONDS:
        return "❌ Access blocked due to repeated failed attempts. Try again later.", 403

    stored_token = session.get('admin_token')
    token_time = session.get('admin_token_time')

    if not stored_token or stored_token != token or now - token_time > 20:
        failed_attempts[ip] += 1
        if failed_attempts[ip] >= BLOCK_THRESHOLD:
            blocked_ips[ip] = now
            failed_attempts[ip] = 0
            print(f"🚫 IP {ip} blocked for 5 minutes.")

        # Send email alert
        try:
            msg = Message(
                subject="🚨 Failed Admin Shortcut Access",
                recipients=[os.getenv("MAIL_USERNAME")],
                body=f"""Failed shortcut access detected:
IP Address: {ip}
Token: {token}
URL Attempted: {request.url}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            )
            mail.send(msg)
        except Exception as e:
            print("❌ Email alert failed:", e)

        return redirect(url_for('index'))

    # Valid shortcut login
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            session.pop('admin_token', None)
            session.pop('admin_token_time', None)
            session['pending_dashboards'] = load_dashboards()
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

# ------------------ Routes ------------------ #
@app.route('/')
def index():
    dashboards = load_dashboards()
    for d in dashboards:
        d['desc'] = format_description(d.get('desc', ''))
    dashboards.sort(key=lambda x: x.get("timestamp", "2000-01-01T00:00:00"), reverse=True)
    current_year = datetime.now().year
    return render_template('index.html', dashboards=dashboards, current_year=current_year)

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('index'))
    dashboards = session.get('pending_dashboards', [])
    dashboards.sort(key=lambda x: x.get("timestamp", "2000-01-01T00:00:00"), reverse=True)
    return render_template('admin.html', dashboards=dashboards)

@app.route('/add_dashboard', methods=['POST'])
def add_dashboard():
    if not session.get('admin'):
        return redirect(url_for('index'))

    title = request.form.get('title')
    category = request.form.get('category')
    desc = request.form.get('desc')
    input_type = request.form.get('input_type')
    link = ''

    if input_type == 'iframe':
        iframe_code = request.form.get('iframe_code', '')
        match = re.search(r'src="([^"]+)"', iframe_code)
        if match:
            link = match.group(1)
    else:
        link = request.form.get('link', '')

    if title and link and category:
        dashboard_id = generate_dashboard_id(title)
        desc_processed = format_description(desc)

        dashboards = session.get('pending_dashboards', [])
        dashboards.append({
            "id": dashboard_id,
            "title": title,
            "link": link,
            "desc": Markup(desc_processed),
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "published": False
        })
        session['pending_dashboards'] = dashboards

        print(f"🔗 Dashboard link: http://localhost:5000/#{dashboard_id}")

    return redirect(url_for('admin'))

@app.route('/delete_dashboard/<int:index>', methods=['POST'])
def delete_dashboard(index):
    if not session.get('admin'):
        return redirect(url_for('index'))

    dashboards = session.get('pending_dashboards', [])
    if 0 <= index < len(dashboards):
        dashboards.pop(index)
        session['pending_dashboards'] = dashboards

    return redirect(url_for('admin'))

@app.route('/save_changes', methods=['POST'])
def save_changes():
    if not session.get('admin'):
        return redirect(url_for('index'))

    dashboards = session.get('pending_dashboards', [])
    save_dashboards(dashboards)

    flash("✅ Changes saved successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    session.pop('pending_dashboards', None)
    return redirect(url_for('index'))

# ------------------ Main ------------------ #
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
