from flask import render_template

from xrf_explorer import app
from file_system.file_upload import UploadFileForm, upload_file


@app.route('/api')
def api():
    return "this is where the API is hosted"


@app.route('/api/info')
def info():
    return "adding more routes is quite trivial"


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    form: UploadFileForm = UploadFileForm()
    if form.validate_on_submit():
        return upload_file(form.file.data, app.config['UPLOAD_FOLDER'])
    return render_template('client/index.html', form=form)
