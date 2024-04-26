from waitress import serve
from xrf_explorer import app

PORT = 8001
BIND_ADDRESS = '127.0.0.1'

if __name__ == '__main__':
    print('Serving on http://localhost:' + str(PORT))
    serve(app, host=BIND_ADDRESS, port=PORT, max_request_body_size=1073741824000000, max_request_header_size=85899345920000)