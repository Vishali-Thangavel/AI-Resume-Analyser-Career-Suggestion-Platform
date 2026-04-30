from flask import Flask, request, jsonify, session, send_from_directory, render_template
from flask_cors import CORS
import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from ai_engine import ResumeAnalyzer
import traceback

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)
app.secret_key = secrets.token_hex(32)
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

analyzer = ResumeAnalyzer()

# ─── DB SETUP ─────────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            subscription TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            content TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            resume_id INTEGER,
            job_role TEXT,
            job_description TEXT,
            score INTEGER,
            result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    db.commit()
    db.close()

init_db()

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def current_user():
    return session.get('user_id')

# ─── PAGES ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyzer')
def analyzer_page():
    return render_template('analyzer.html')

@app.route('/result')
def result_page():
    return render_template('result.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/builder')
def builder_page():
    return render_template('builder.html')

# ─── AUTH API ─────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if not username or not email or not password:
        return jsonify({'error': 'All fields required'}), 400
    db = get_db()
    try:
        db.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                   (username, email, hash_password(password)))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['subscription'] = user['subscription']
        return jsonify({'message': 'Registered', 'username': username, 'subscription': 'free'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 409
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email=? AND password=?',
                      (email, hash_password(password))).fetchone()
    db.close()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['subscription'] = user['subscription']
    return jsonify({'message': 'Logged in', 'username': user['username'], 'subscription': user['subscription']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/me')
def me():
    if not current_user():
        return jsonify({'logged_in': False})
    return jsonify({'logged_in': True, 'username': session.get('username'), 'subscription': session.get('subscription')})

# ─── ANALYZE ──────────────────────────────────────────────────────────────────

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        resume_text = ''
        job_role = ''
        job_description = ''

        if request.content_type and 'multipart' in request.content_type:
            job_role = request.form.get('job_role', '')
            job_description = request.form.get('job_description', '')
            resume_text = request.form.get('resume_text', '')
            file = request.files.get('resume_file')
            if file and file.filename:
                from file_parser import parse_file
                resume_text = parse_file(file)
        else:
            data = request.json or {}
            resume_text = data.get('resume_text', '')
            job_role = data.get('job_role', '')
            job_description = data.get('job_description', '')

        if not resume_text.strip():
            return jsonify({'error': 'Resume text is required'}), 400

        result = analyzer.analyze(resume_text, job_role, job_description)

        # Persist if logged in
        user_id = current_user()
        if user_id:
            import json
            db = get_db()
            res = db.execute('INSERT INTO resumes (user_id, content) VALUES (?, ?)',
                             (user_id, resume_text))
            resume_id = res.lastrowid
            db.execute('INSERT INTO analyses (user_id, resume_id, job_role, job_description, score, result_json) VALUES (?,?,?,?,?,?)',
                       (user_id, resume_id, job_role, job_description, result['score'], json.dumps(result)))
            db.commit()
            db.close()

        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ─── HISTORY ──────────────────────────────────────────────────────────────────

@app.route('/api/history')
def history():
    user_id = current_user()
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    import json
    db = get_db()
    rows = db.execute(
        'SELECT * FROM analyses WHERE user_id=? ORDER BY created_at DESC LIMIT 20', (user_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
