from pathlib import Path

from flask import Flask, send_from_directory

app = Flask(__name__, template_folder=Path('client/templates'), static_folder='client/dist')
app.config['SECRET_KEY'] = 'insert-more-secure-key'
app.config['UPLOAD_FOLDER'] = 'server/files'


from xrf_explorer.server import routes


# All routes not matched in the server are forwarded to the client
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory(Path('client/dist'), path)