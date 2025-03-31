import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1 * 1000 * 1000  # 1 MB
app.secret_key = 'supersecretkey'

# 🧠 HTML Template
HTML_TEMPLATE = '''
<!doctype html>
<title>📁 Flask File Manager</title>
<h1>Directory: /{{ rel_path }}</h1>

<!-- Upload Form -->
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

<!-- Create Folder -->
<h3>Create New Folder</h3>
<form method=post action="{{ url_for('create_dir', subdir=rel_path) }}">
  <input type=text name=folder placeholder="Folder name" required>
  <input type=submit value="Create Folder">
</form>

<!-- Go Back -->
{% if rel_path %}
  <p><a href="{{ url_for('browse', subdir=parent_path) }}">⬅️ Back</a></p>
{% endif %}

<!-- File/Folder List -->
<ul>
  {% for item in items %}
    <li>
      {% if item.is_dir %}
        📁 <a href="{{ url_for('browse', subdir=item.rel_path) }}">{{ item.name }}</a>
        <form method=post action="{{ url_for('delete_dir', subdir=item.rel_path) }}" style="display:inline">
          <button type="submit">❌</button>
        </form>
      {% else %}
        📄 {{ item.name }} - 
        <a href="{{ url_for('download_file', subdir=rel_path, filename=item.name) }}">Download</a>
      {% endif %}
    </li>
  {% endfor %}
</ul>
'''

# ✅ Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_path(subdir=""):
    full = os.path.abspath(os.path.join(UPLOAD_FOLDER, subdir))
    return full if full.startswith(UPLOAD_FOLDER) else UPLOAD_FOLDER

# ✅ Browse files/folders
@app.route('/', defaults={'subdir': ''})
@app.route('/dir/<path:subdir>')
def browse(subdir):
    full_path = safe_path(subdir)
    parent_path = os.path.dirname(subdir)
    items = []
    folders = []

    for name in os.listdir(full_path):
        path = os.path.join(full_path, name)
        rel = os.path.join(subdir, name).replace("\\", "/")
        items.append({'name': name, 'is_dir': os.path.isdir(path), 'rel_path': rel})
        if os.path.isdir(path):
            folders.append(rel)

    return render_template_string(HTML_TEMPLATE, items=items, rel_path=subdir, parent_path=parent_path, folders=folders)

# ✅ Upload file to selected folder
@app.route('/upload_to_selected', methods=['POST'])
def upload_file_to_selected():
    file = request.files.get('file')
    target_dir = request.form.get('target_dir', '')

    if not file or file.filename == '':
        return "No file selected", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        target_path = safe_path(target_dir)
        os.makedirs(target_path, exist_ok=True)
        file.save(os.path.join(target_path, filename))
        return redirect(url_for('browse', subdir=target_dir))

    return "Invalid file type", 400

# ✅ Create a new folder
@app.route('/create/', defaults={'subdir': ''}, methods=['POST'])
@app.route('/create/<path:subdir>', methods=['POST'])
def create_dir(subdir):
    folder = request.form.get('folder')
    if folder:
        new_dir = os.path.join(safe_path(subdir), secure_filename(folder))
        os.makedirs(new_dir, exist_ok=True)
    return redirect(url_for('browse', subdir=subdir))

# ✅ Delete an empty folder
@app.route('/delete/<path:subdir>', methods=['POST'])
def delete_dir(subdir):
    target = safe_path(subdir)
    if os.path.isdir(target) and len(os.listdir(target)) == 0:
        os.rmdir(target)
    return redirect(url_for('browse', subdir=os.path.dirname(subdir)))

# ✅ Download file
@app.route('/download/<path:subdir>/<filename>')
def download_file(subdir, filename):
    folder = safe_path(subdir)
    return send_from_directory(folder, filename, as_attachment=True)

# ✅ Startup
if __name__ == "__main__":
    print(f"📂 File system root: {UPLOAD_FOLDER}")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
