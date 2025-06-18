from flask import Flask, flash, render_template, request, redirect, url_for, session
from datetime import datetime
from markupsafe import Markup
from dotenv import load_dotenv
import json, os, re, uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

DATA_FILE = "dashboards.json"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

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

# ------------------ Routes ------------------ #
@app.route('/')
def index():
    dashboards = load_dashboards()
    for d in dashboards:
        d['desc'] = format_description(d.get('desc', ''))

    dashboards.sort(key=lambda x: x.get("timestamp", "2000-01-01T00:00:00"), reverse=True)
    current_year = datetime.now().year
    return render_template('index.html', dashboards=dashboards, current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            session['pending_dashboards'] = load_dashboards()
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

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
