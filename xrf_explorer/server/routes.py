from xrf_explorer import app

@app.route('/api')
def api():
    return "this is where the API is hosted"

@app.route('/api/info')
def info():
    return "adding more routes is quite trivial"