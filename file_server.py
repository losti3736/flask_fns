from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for
import os

app = Flask(__name__)

# Base directory for file storage
BASE_DIR = os.path.abspath("nfs_files")
os.makedirs(BASE_DIR, exist_ok=True)

# HTML template
HTML = """
<!doctype html>
<title>Network File System</title>
<h2>📁 Current Directory: /{{ rel_path }}</h2>

<!-- Upload Form -->
<form method="POST" action="{{ url_for('upload', path=rel_path) }}" enctype="multipart/form-data">
  <input type="file" name="file" required>
  <input type="submit" value="Upload File">
</form>


<!-- Create Folder Form -->
<form method="POST" action="{{ url_for('mkdir', path=rel_path) }}">
  <input type="text" name="foldername" placeholder="Folder name" required>
  <input type="submit" value="Create Folder">
</form>

<!-- File & Folder Listing -->
<ul>
  {% if rel_path %}
    <li><a href="{{ url_for('browse', path=parent_path) }}">⬅️ Go Back</a></li>
  {% endif %}
  {% for item in items %}
    <li>
      {% if item.is_dir %}
        📁 <a href="{{ url_for('browse', path=item.rel_path) }}">{{ item.name }}</a>
      {% else %}
        📄 {{ item.name }} - <a href="{{ url_for('download', path=item.rel_path) }}">Download</a>
      {% endif %}
    </li>
  {% endfor %}
</ul>
"""

# Helper: Prevent path traversal
def safe_path(path=""):
    full = os.path.abspath(os.path.join(BASE_DIR, path))
    return full if full.startswith(BASE_DIR) else BASE_DIR

@app.route("/", defaults={"path": ""})
@app.route("/browse/<path:path>")
def browse(path):
    full_path = safe_path(path)
    items = []
    for name in os.listdir(full_path):
        rel = os.path.relpath(os.path.join(path, name)).replace("\\", "/")
        items.append({
            "name": name,
            "is_dir": os.path.isdir(os.path.join(full_path, name)),
            "rel_path": rel
        })
    parent_path = os.path.dirname(path)
    return render_template_string(HTML, items=items, rel_path=path, parent_path=parent_path)

@app.route("/upload/<path:path>", methods=["POST"])
def upload(path):
    path = path or ""  # Default to base directory if path is empty
    file = request.files.get("file")
    if file:
        dest = safe_path(path)
        if not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)
        file.save(os.path.join(dest, file.filename))
    return redirect(url_for("browse", path=path))

@app.route("/mkdir/<path:path>", methods=["POST"])
def mkdir(path):
    foldername = request.form.get("foldername", "").strip()
    if foldername:
        new_dir = os.path.join(safe_path(path), foldername)
        os.makedirs(new_dir, exist_ok=True)
    return redirect(url_for("browse", path=path))


@app.route("/download/<path:path>")
def download(path):
    full_path = safe_path(path)
    return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=True)

if __name__ == "__main__":
    print(f"📂 File system root: {BASE_DIR}")
    app.run(debug=True)
