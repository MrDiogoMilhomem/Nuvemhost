from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort, jsonify, make_response
import mysql.connector
from bcrypt import hashpw, gensalt, checkpw
from werkzeug.utils import secure_filename
import os
import zipfile
import shutil
from datetime import datetime
import re
import mimetypes
from functools import wraps
from uuid import uuid4
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from json import loads

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

def setup_logging():
    handler = RotatingFileHandler(os.getenv("LOG_FILE"), maxBytes=1000000, backupCount=3)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)

    # Logger do Flask app
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Logger do Werkzeug (logs de requisição HTTP)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addHandler(handler)
    werkzeug_logger.setLevel(logging.INFO)

# setup_logging()

# Database configuration
DB_CONFIG = {
    'host':     os.getenv("DB_HOST"),
    'user':     os.getenv("DB_USER"),
    'password': os.getenv("DB_PASS"),
    'database': os.getenv("DB_NAME")
}

# Upload configuration
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
ALLOWED_EXTENSIONS = loads(os.getenv("ALLOWED_EXTENSIONS"))
ALLOWED_PROJECT_FILES = loads(os.getenv("ALLOWED_PROJECT_FILES"))

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_safe_project_file(filename):
    """Check if project file is safe to serve"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in ALLOWED_PROJECT_FILES

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def generate_password_hash(senha:str):
    return hashpw(senha.encode("utf-8"), gensalt())

def check_password_hash(hash:str, senha:str):
    return checkpw(senha.encode("utf-8"), hash.encode("utf-8"))

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        if not validate_username(username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores.', 'danger')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'danger')
            return render_template('register.html')
        
        try:
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                flash('Username or email already exists.', 'danger')
                return render_template('register.html')
            
            # Create user
            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            conn.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.Error as e:
            flash('Registration failed. Please try again.', 'danger')
            print(f"Registration error: {e}")
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'danger')
            return render_template('login.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
                
        except mysql.connector.Error as e:
            flash('Login failed. Please try again.', 'danger')
            print(f"Login error: {e}")
        finally:
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, project_name, upload_date, status FROM projects WHERE user_id = %s ORDER BY upload_date DESC",
            (session['user_id'],)
        )
        projects = cursor.fetchall()

        print(f"dash ativado: INFO: {projects}")
        
        return render_template('dashboard.html', projects=projects, project_count=len(projects))
        
    except mysql.connector.Error as e:
        flash('Error loading dashboard.', 'danger')
        print(f"Dashboard error: {e}")
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_project():
    """Upload new project"""
    if request.method == 'POST':
        # Check project limit
        conn = get_db_connection()
        if not conn:
            flash('Database connection error.', 'danger')
            return redirect(url_for('dashboard'))
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = %s", (session['user_id'],))
            project_count = cursor.fetchone()[0]
            
            if project_count >= 3:
                flash('You have reached the maximum limit of 3 projects.', 'warning')
                return redirect(url_for('dashboard'))
            
            project_name = request.form.get('project_name', '').strip()
            if not project_name:
                flash('Project name is required.', 'danger')
                return render_template('upload.html')
            
            if 'project_file' not in request.files:
                flash('No file selected.', 'danger')
                return render_template('upload.html')
            
            file = request.files['project_file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return render_template('upload.html')
            
            if not allowed_file(file.filename):
                flash('Only ZIP files are allowed.', 'danger')
                return render_template('upload.html')
            
            # Create project directory
            project_id = str(uuid4())
            print(project_id)
            project_dir = os.path.join(UPLOAD_FOLDER, project_id)
            os.makedirs(project_dir, exist_ok=True)
            
            # Save and extract ZIP file
            filename = secure_filename(file.filename)
            zip_path = os.path.join(project_dir, filename)
            file.save(zip_path)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Extract files safely
                    for member in zip_ref.namelist():
                        if member.startswith('/') or '..' in member:
                            continue  # Skip dangerous paths
                        
                        # Check file extension
                        if '.' in member:
                            ext = member.rsplit('.', 1)[1].lower()
                            if ext not in ALLOWED_PROJECT_FILES:
                                continue
                        
                        zip_ref.extract(member, project_dir)
                
                # Remove ZIP file after extraction
                os.remove(zip_path)
                
                # Check for index.html
                index_path = os.path.join(project_dir, 'index.html')
                if not os.path.exists(index_path):
                    # Look for HTML files in subdirectories
                    html_found = False
                    for root, dirs, files in os.walk(project_dir):
                        for file in files:
                            if file.endswith('.html'):
                                html_found = True
                                break
                        if html_found:
                            break
                    
                    if not html_found:
                        shutil.rmtree(project_dir)
                        flash('No HTML files found in the project.', 'danger')
                        return render_template('upload.html')
                
                # Save project to database
                cursor.execute(
                    "INSERT INTO projects (id, user_id, project_name, folder_path, upload_date) VALUES (%s, %s, %s, %s, %s)",
                    (project_id, session['user_id'], project_name, f"{project_id}", datetime.now())
                )
                conn.commit()
                
                flash('Project uploaded successfully!', 'success')
                return redirect(url_for('dashboard'))
                
            except zipfile.BadZipFile:
                shutil.rmtree(project_dir)
                flash('Invalid ZIP file.', 'danger')
                return render_template('upload.html')
            
        except mysql.connector.Error as e:
            flash('Upload failed. Please try again.', 'danger')
            print(f"Upload error: {e}")
        finally:
            conn.close()
    
    return render_template('upload.html')

@app.route('/edit_project/<project_id>')
@login_required
def edit_project(project_id):
    """Edit project files"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT project_name, folder_path FROM projects WHERE id = %s AND user_id = %s",
            (project_id, session['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            flash('Project not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        project_name, folder_path = project
        project_dir = os.path.join(UPLOAD_FOLDER, folder_path)
        
        # Get all editable files
        files = []
        for root, dirs, filenames in os.walk(project_dir):
            for filename in filenames:
                if is_safe_project_file(filename):
                    rel_path = os.path.relpath(os.path.join(root, filename), project_dir)
                    files.append(rel_path)
        
        return render_template('edit_project.html', 
            project_id=project_id, 
            project_name=project_name, 
            files=files
        )
        
    except mysql.connector.Error as e:
        flash('Error loading project.', 'danger')
        print(f"Edit project error: {e}")
        return redirect(url_for('dashboard'))
    finally:
        conn.close()

@app.route('/get_file_content/<project_id>/<path:file_path>')
@login_required
def get_file_content(project_id, file_path):
    """Get file content for editing"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT folder_path FROM projects WHERE id = %s AND user_id = %s",
            (project_id, session['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        project_dir = os.path.join(UPLOAD_FOLDER, project[0])
        full_path = os.path.join(project_dir, file_path)
        
        # Security check
        if not os.path.abspath(full_path).startswith(os.path.abspath(project_dir)):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content})
        except UnicodeDecodeError:
            return jsonify({'error': 'File is not text-based'}), 400
        
    except mysql.connector.Error as e:
        return jsonify({'error': 'Database error'}), 500
    finally:
        conn.close()

@app.route('/save_file_content/<project_id>/<path:file_path>', methods=['POST'])
@login_required
def save_file_content(project_id, file_path):
    """Save file content"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT folder_path FROM projects WHERE id = %s AND user_id = %s",
            (project_id, session['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        project_dir = os.path.join(UPLOAD_FOLDER, project[0])
        full_path = os.path.join(project_dir, file_path)
        
        # Security check
        if not os.path.abspath(full_path).startswith(os.path.abspath(project_dir)):
            return jsonify({'error': 'Invalid file path'}), 403
        
        content = request.json.get('content', '')
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        
    except mysql.connector.Error as e:
        return jsonify({'error': 'Database error'}), 500
    finally:
        conn.close()

@app.route('/delete_project/<project_id>')
@login_required
def delete_project(project_id):
    print(f"delete {project_id}")
    """Delete a project"""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT folder_path FROM projects WHERE id = %s AND user_id = %s",
            (project_id, session['user_id'])
        )
        project = cursor.fetchone()
        
        if not project:
            flash('Project not found.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Delete project files
        project_dir = os.path.join(UPLOAD_FOLDER, project[0])
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        
        # Delete from database
        cursor.execute("DELETE FROM projects WHERE id = %s AND user_id = %s", (project_id, session['user_id']))
        conn.commit()
        
        flash('Project deleted successfully.', 'success')
        
    except mysql.connector.Error as e:
        flash('Error deleting project.', 'danger')
        print(f"Delete error: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/toggle_project_status/<project_id>', methods=['POST'])
@login_required
def toggle_project_status(project_id):
    """Toggle project status between active and paused"""
    print(f"toggle_project_status called: project_id={project_id}, user_id={session.get('user_id')}")
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, project_name FROM projects WHERE id = %s AND user_id = %s",
            (project_id, session['user_id'])
        )
        project = cursor.fetchone()
        print(f"Project found: {project}")
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        current_status = project[0]
        project_name = project[1]
        new_status = 'paused' if current_status == 'active' else 'active'
        print(f"Changing status from {current_status} to {new_status}")
        
        cursor.execute(
            "UPDATE projects SET status = %s WHERE id = %s AND user_id = %s",
            (new_status, project_id, session['user_id'])
        )
        conn.commit()
        
        action = 'paused' if new_status == 'paused' else 'reactivated'
        return jsonify({
            'success': True,
            'new_status': new_status,
            'message': f'Project "{project_name}" has been {action}.'
        })
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        conn.close()

@app.route('/project/<project_id>/')
@app.route('/project/<project_id>/<path:filename>')
def serve_project(project_id, filename='index.html'):
    """Serve project files publicly"""
    
    # Check if project exists
    conn = get_db_connection()
    if not conn:
        abort(500)
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT p.folder_path, p.status, p.project_name FROM projects p 
               JOIN users u ON p.user_id = u.id 
               WHERE p.folder_path LIKE %s""",
            (project_id,)
        )
        project = cursor.fetchone()
        
        if not project:
            abort(404)
        
        # Check project status
        if project[1] == 'paused':
            return render_template('paused.html', project_name=project[2])
        
        project_dir = os.path.join(UPLOAD_FOLDER, project[0])
        
        # Security check: ensure file is within project directory
        file_path = os.path.join(project_dir, filename)
        if not os.path.abspath(file_path).startswith(os.path.abspath(project_dir)):
            abort(403)
        
        # Check if file exists and is safe
        if not os.path.exists(file_path):
            abort(404)
        
        if not is_safe_project_file(filename):
            abort(403)
        
        # Serve file with appropriate MIME type
        mimetype = mimetypes.guess_type(file_path)[0]
        return send_from_directory(project_dir, filename, mimetype=mimetype)
        
    except mysql.connector.Error as e:
        print(f"Serve project error: {e}")
        abort(500)
    finally:
        conn.close()

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/service-worker.js')
def serve_sw():
    return send_from_directory('static/js', 'service-worker.js', mimetype='application/javascript')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("DEBUG"))
