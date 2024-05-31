import logging

from waitress import serve

from xrf_explorer import app

# from flask_cors import CORS
# CORS(app)

LOG: logging.Logger = logging.getLogger(__name__)

PORT = 8001
BIND_ADDRESS = '127.0.0.1'

if __name__ == '__main__':
    # set up logger
    logging.basicConfig(
        level=logging.INFO,             # lowest logging level used
        # filename="logs/log.log",        # path to log file to output instead of console
        # filemode="w",                   # access mdoe to file specified in `filename`
        format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
        )

    LOG.info('Serving on http://localhost:' + str(PORT))
    serve(app, host=BIND_ADDRESS, port=PORT, max_request_body_size=1073741824000000, max_request_header_size=85899345920000)
