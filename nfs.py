import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1000 * 1000 # 100 MB limit

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # 🧠 Return a download link instead of redirecting
            return f'''
            <!doctype html>
            <title>Upload Successful</title>
            <h1>✅ File uploaded!</h1>
            <p><a href="/uploads/{filename}">Click here to download {filename}</a></p>
            <p><a href="/">Upload another file</a></p>
            '''
    # HTML form (for GET request)
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File (.txt, .pdf)</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file required>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == "__main__":
    print(f"📂 File system root: {UPLOAD_FOLDER}")
    app.run(debug=True)