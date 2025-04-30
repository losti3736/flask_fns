import os
import json
from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string, session
import shutil

from werkzeug.utils import secure_filename
from flask import session


import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name='dlpfxvtbq',
    api_key='331597429749235',
    api_secret='nMmRWf5jTJsnh-l8KUV4qlTCN9k',
    secure=True
)


UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py'}

# User database file
USERS_FILE = os.path.join('/tmp', 'users.json')
# Tracks uploaded Cloudinary files per user
USER_FILES = os.path.join('/tmp', 'user_files.json')


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1000 * 1000  # 1 MB
app.secret_key = 'supersecretkey'  # Needed for sessions

@app.before_request
def log_request_info():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    port = request.environ.get('REMOTE_PORT', 'unknown')
    method = request.method
    path = request.path

    print(f"[HTTP REQUEST] {method} {path} from {ip}:{port}")


# Load users from file or create empty dict
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)



def load_user_files():
    if os.path.exists(USER_FILES):
        with open(USER_FILES, 'r') as f:
            return json.load(f)
    return {}

def save_user_files(data):
    with open(USER_FILES, 'w') as f:
        json.dump(data, f, indent=2)


# HTML Templates
REGISTER_TEMPLATE = '''
<!doctype html>
<title>Register</title>
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f0f8ff;
        margin: 0;
        padding: 20px;
    }
    .register-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 20px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h2 {
        color: #1e90ff;
        text-align: center;
    }
    input[type="text"], input[type="password"] {
        width: 100%;
        padding: 10px;
        margin: 8px 0;
        border: 1px solid #1e90ff;
        border-radius: 4px;
        box-sizing: border-box;
    }
    input[type=submit] {
        width: 100%;
        background-color: #1e90ff;
        color: white;
        padding: 10px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 10px;
    }
    input[type=submit]:hover {
        background-color: #187bcd;
    }
    .error {
        color: #ff0000;
        text-align: center;
    }
    .login-link {
        text-align: center;
        margin-top: 20px;
    }
    .login-link a {
        color: #1e90ff;
        text-decoration: none;
    }
    .login-link a:hover {
        text-decoration: underline;
    }
</style>
<div class="register-container">
    <h2>Register</h2>
    <form method="post" action="{{ url_for('register') }}">
        <input type="text" name="username" placeholder="Username" required><br><br>
        <input type="password" name="password" placeholder="Password" required><br><br>
        <input type=submit value="Register">
    </form>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <div class="login-link">
        Already have an account? <a href="{{ url_for('login') }}">Login</a>
    </div>
</div>
'''

LOGIN_TEMPLATE = '''
<!doctype html>
<title>Login</title>
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f0f8ff;
        margin: 0;
        padding: 20px;
    }
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 20px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h2 {
        color: #1e90ff;
        text-align: center;
    }
    input[type="text"], input[type="password"] {
        width: 100%;
        padding: 10px;
        margin: 8px 0;
        border: 1px solid #1e90ff;
        border-radius: 4px;
        box-sizing: border-box;
    }
    input[type=submit] {
        width: 100%;
        background-color: #1e90ff;
        color: white;
        padding: 10px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    input[type=submit]:hover {
        background-color: #187bcd;
    }
    .error {
        color: #ff0000;
        text-align: center;
    }
    .register-link {
        text-align: center;
        margin-top: 20px;
    }
    .register-link a {
        color: #1e90ff;
        text-decoration: none;
    }
    .register-link a:hover {
        text-decoration: underline;
    }
</style>
<div class="login-container">
    <h2>Login</h2>
    <form method="post" action="{{ url_for('login') }}">
        <input type="text" name="username" placeholder="Username" required><br><br>
        <input type="password" name="password" placeholder="Password" required><br><br>
        <input type=submit value="Login">
    </form>
    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}
    <div class="register-link">
        Don't have an account? <a href="{{ url_for('register') }}">Register</a>
    </div>
</div>
'''

HTML_TEMPLATE = '''
<!doctype html>
<title>Flask File Manager</title>
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f0f8ff;
        margin: 0;
        padding: 20px;
    }
    .container {
        max-width: 1200px;
        margin: 0 auto;
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #1e90ff;
    }
    .username {
        font-size: 24px;
        font-weight: bold;
        color: #1e90ff;
        margin: 0;
    }
    .logout {
        margin-bottom: 20px;
    }
    .logout a {
        color: #1e90ff;
        text-decoration: none;
        padding: 8px 16px;
        border: 1px solid #1e90ff;
        border-radius: 4px;
        transition: all 0.3s;
    }
    .logout a:hover {
        background-color: #1e90ff;
        color: white;
    }
    .file-list {
        margin-top: 20px;
    }
    .move-form {
        display: inline;
        margin-left: 10px;
    }
    .back-link {
        color: #1e90ff;
        text-decoration: none;
        display: inline-block;
        margin: 10px 0;
    }
    .back-link:hover {
        text-decoration: underline;
    }
    .form-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 4px;
        margin: 15px 0;
    }
    input[type="file"], input[type="text"], select {
        padding: 8px;
        border: 1px solid #1e90ff;
        border-radius: 4px;
        margin-right: 10px;
    }
    button, input[type=submit] {
        background-color: #1e90ff;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    button:hover, input[type=submit]:hover {
        background-color: #187bcd;
    }
    ul {
        list-style-type: none;
        padding: 0;
    }
    li {
        padding: 10px;
        margin: 5px 0;
        background-color: #f8f9fa;
        border-radius: 4px;
        display: flex;
        align-items: center;
    }
    li:hover {
        background-color: #e9ecef;
    }
    a {
        color: #1e90ff;
        text-decoration: none;
        margin-right: 10px;
    }
    a:hover {
        text-decoration: underline;
    }
    .file-icon {
        margin-right: 10px;
    }
    .move-form select {
        padding: 6px;
        border: 1px solid #1e90ff;
        border-radius: 4px;
        margin: 0 5px;
    }
    .size-limit {
        text-align: left;
        color: #666;
        font-size: 0.9em;
        margin-top: 5px;
        margin-left: 5px;
        font-style: italic;
    }
</style>

<div class="container">
    <div class="header">
        <h1 class="username">{{ session.username }}'s Files</h1>
        <div class="logout">
            <a href="{{ url_for('logout') }}">Logout</a>
        </div>
    </div>

    <div class="form-container">
        <h3>Upload to Selected Folder</h3>
        <form method=post enctype=multipart/form-data action="{{ url_for('upload_file_to_selected') }}">
            <input type=file name=file required>
            <label for="target_dir">Choose a folder:</label>
            <select name="target_dir">
                {% for folder in folders %}
                    <option value="{{ folder }}">{{ folder }}</option>
                {% endfor %}
            </select>
            <input type=submit value="Upload File">
        </form>
        <div class="size-limit">Files must be less than 10 MB in size</div>
    </div>

    <div class="form-container">
        <h3>Create New Folder</h3>
        <form method=post action="{{ url_for('create_dir', subdir=rel_path) }}">
            <input type=text name=folder placeholder="Folder name" required>
            <input type=submit value="Create Folder">
        </form>
    </div>

    {% if rel_path %}
        <a href="{{ url_for('browse', subdir=parent_path) }}" class="back-link">← Back</a>
    {% endif %}

    <div class="file-list">
        <ul>
            {% for item in items %}
                <li>
                    <span class="file-icon">{% if item.is_dir %}📁{% else %}📄{% endif %}</span>
                    <a href="{{ url_for('browse', subdir=item.rel_path) if item.is_dir else url_for('download_file', subdir=rel_path, filename=item.name) }}">
                        {{ item.name }}
                    </a>
                    {% if item.is_dir %}
                        <form method="post" action="{{ url_for('delete_dir', subdir=item.rel_path) }}" style="display:inline" onsubmit="return confirmDelete('{{ item.name }}')">
                            <button type=submit>Delete</button>
                        </form>
                    {% else %}
                        <form class="move-form" method="post" action="{{ url_for('move_file', subdir=rel_path, filename=item.name) }}">
                            <label for="target_dir">Move to:</label>
                            <select name="target_dir" required>
                                {% for folder in folders %}
                                    <option value="{{ folder }}">{{ folder }}</option>
                                {% endfor %}
                            </select>
                            <button type=submit>Move</button>
                        </form>
                    {% endif %}
                </li>
            {% endfor %}
        </ul>
    </div>
    {% if uploaded_files %}
    <div class="form-container">
        <h3>Cloudinary Uploaded Files</h3>
        <ul>
            {% for file in uploaded_files %}
            <li><a href="{{ file.url }}" target="_blank">{{ file.filename }}</a></li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

</div>
<script>
function confirmDelete(folderName) {
    return confirm(`Are you sure you want to delete the folder "${folderName}"? This will permanently remove all its contents.`);
}
</script>
'''

# Checks file extension to see if it's allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensures flask is using the correct folder path for the user
def safe_path(subdir=""):
    user_folder = session.get('username')
    if not user_folder:
        print("[ERROR] No user session found")
        return UPLOAD_FOLDER  # fallback path must still exist

    user_upload_folder = os.path.join(UPLOAD_FOLDER, secure_filename(user_folder))
    full = os.path.abspath(os.path.join(user_upload_folder, subdir))

    if not full.startswith(user_upload_folder):
        return user_upload_folder
    return full


def login_required(func):
    # Decorator to protect routes
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error = 'Username and password are required'
        else:
            users = load_users()
            if username in users:
                error = 'Username already exists'
            else:
                # Create user directory
                user_dir = os.path.join(UPLOAD_FOLDER, secure_filename(username))
                os.makedirs(user_dir, exist_ok=True)
                
                # Save user credentials
                users[username] = password
                save_users(users)
                
                return redirect(url_for('login'))

    return render_template_string(REGISTER_TEMPLATE, error=error)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users = load_users()
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('browse'))
        else:
            error = 'Invalid username or password'

    return render_template_string(LOGIN_TEMPLATE, error=error)

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Browse shows list of files/folders for given directory (subdir)
@app.route('/', defaults={'subdir': ''})
@app.route('/dir/<path:subdir>')
@login_required
def browse(subdir):
    full_path = safe_path(subdir)
    parent_path = os.path.dirname(subdir)
    items = []

    # ✅ Check if the path exists
    if not os.path.exists(full_path):
        print(f"[ERROR] Requested path does not exist: {full_path}")
        return f"Directory '{subdir}' does not exist.", 404

    try:
        for name in os.listdir(full_path):
            path = os.path.join(full_path, name)
            rel = os.path.join(subdir, name).replace("\\", "/")
            items.append({'name': name, 'is_dir': os.path.isdir(path), 'rel_path': rel})
    except Exception as e:
        print(f"[ERROR] Failed to list directory '{full_path}': {e}")
        return f"Error accessing directory: {e}", 500

    folders = get_all_folders()

    username = session.get('username')
    uploaded_files = load_user_files().get(username, [])

    return render_template_string(
        HTML_TEMPLATE,
        items=items,
        rel_path=subdir,
        parent_path=parent_path,
        folders=folders,
        uploaded_files=uploaded_files
    )



# Upload file to Cloudinary instead of saving locally
@app.route('/upload_to_selected', methods=['POST'])
@login_required
def upload_file_to_selected():
    file = request.files.get('file')

    if not file or file.filename == '':
        return "No file selected", 400

    if file and allowed_file(file.filename):
        try:
            result = cloudinary.uploader.upload(file)
            file_url = result['secure_url']
            return f"File uploaded successfully: <a href='{file_url}' target='_blank'>View file</a>"
        except Exception as e:
            return f"Upload error: {str(e)}", 500

    return "Invalid file type", 400


# Create a new folder 
@app.route('/create/', defaults={'subdir': ''}, methods=['POST'])
@app.route('/create/<path:subdir>', methods=['POST'])
@login_required
def create_dir(subdir):
    folder = request.form.get('folder')
    if folder:
        # Place the new folder in the correct directory
        new_dir = os.path.join(safe_path(subdir), secure_filename(folder))
        os.makedirs(new_dir, exist_ok=True)
    return redirect(url_for('browse', subdir=subdir))

# Delete a folder
@app.route('/delete/<path:subdir>', methods=['POST'])
@login_required
def delete_dir(subdir):
    target = safe_path(subdir)
    
    if os.path.exists(target):
        if os.path.isdir(target):
            try:
                # If directory is not empty, remove all contents
                shutil.rmtree(target)
                print(f"Deleted folder: {target}")
            except Exception as e:
                print(f"Error deleting folder {target}: {e}")
                return f"Error deleting folder: {e}", 500
        else:
            print(f"Path is not a directory: {target}")
            return "Target is not a directory", 400
    else:
        print(f"Path does not exist: {target}")
        return "Directory does not exist", 404

    parent_dir = os.path.dirname(subdir)
    return redirect(url_for('browse', subdir=parent_dir))


# Download file 
@app.route('/download/<path:subdir>/<filename>')
@login_required
def download_file(subdir, filename):
    folder = safe_path(subdir)
    return send_from_directory(folder, filename, as_attachment=True)

# Move file to another folder 
@app.route('/move/<path:subdir>/<filename>', methods=['POST'])
@login_required
def move_file(subdir, filename):
    target_dir = request.form.get('target_dir', '')
    if not target_dir:
        return "No target directory specified", 400

    source_path = safe_path(subdir)
    target_path = safe_path(target_dir)
    
    # Ensure the target directory exists
    os.makedirs(target_path, exist_ok=True)
    
    source_file = os.path.join(source_path, filename)
    target_file = os.path.join(target_path, filename)
    
    if not os.path.exists(source_file):
        return "Source file not found", 404
    
    if os.path.exists(target_file):
        return "File already exists in target directory", 400
    
    # Try to move the file
    try:
        shutil.move(source_file, target_file)
        return redirect(url_for('browse', subdir=subdir))
    except Exception as e:
        return f"Error moving file: {str(e)}", 500

# Get all folders recursively for the dropdown
def get_all_folders(base_path="", rel_base=""):
    folders = []

    # Get the user's root path only once (in browse route)
    if rel_base == "":
        root = safe_path()
    else:
        root = os.path.join(safe_path(), base_path)

    full_path = os.path.abspath(root)
    try:
        for entry in os.scandir(full_path):
            if entry.is_dir():
                rel_path = os.path.join(rel_base, entry.name).replace("\\", "/")
                folders.append(rel_path)
                # Recurse into subfolders
                folders.extend(get_all_folders(os.path.join(base_path, entry.name), rel_path))
    except Exception as e:
        print(f"[ERROR] Scanning folder failed: {e}")

    return folders


@app.before_request
def setup_user_folders():
    # Create upload folder for the first time running
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

# Driver
# if __name__ == "__main__":
#     print(f"📂 File system root: {UPLOAD_FOLDER}")
#     os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#     app.run(debug=True)
 
# if __name__ == "__main__":
#     import socket
#     import os

#     port = int(os.environ.get("PORT", 5000))
#     hostname = socket.gethostname()
#     ip = socket.gethostbyname(hostname)

#     print(f"🟢 Starting Flask app on {ip}:{port}")
#     print(f"📂 File system root: {UPLOAD_FOLDER}")
#     os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#     app.run(host='0.0.0.0', port=port, debug=True)

