# Main file to run the XRF-Explorer server
import argparse
import logging

from datetime import datetime
from os import environ
from sys import stdout

LOG: logging.Logger = logging.getLogger(__name__)

# set up commandline argument parser
parser: argparse.ArgumentParser = argparse.ArgumentParser(
    prog="python run.py", description="XRF-Explorer")
parser.add_argument("-c", "--config", dest="config", default="config/backend.yml", metavar="PATH",
                    help="path to the XRF-Explorer configuration file")
parser.add_argument("-l", "--log", dest="loglevel", default="INFO", metavar="LEVEL",
                    help="set logging level, can be any of CRITICAL, ERROR, WARN, INFO, DEBUG")

if __name__ == '__main__':
    # read commandline arguments
    args = parser.parse_args()

    # set logging level
    loglevel = logging.getLevelName(args.loglevel)

    # set logging output handlers, logging is always printed to console
    outputHandlers: list[logging.Handler] = [logging.StreamHandler(stdout)]
    mode: str | None = environ.get("XRF_EXPLORER_LOG_MODE")
    # on the server, we also want the logging to be sent to a log file
    if mode == "PROD":
        currentTime: str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        outputHandlers.append(logging.FileHandler(f"logs/log_{currentTime}.log"))

    # set up logger
    logging.basicConfig(
        level=loglevel,  # lowest logging level used
        format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
        handlers=outputHandlers  # set output handler
    )

    LOG.info("Starting XRF-Explorer")
    # import app dependencies only after showing initial log message
    from waitress import serve
    from xrf_explorer import app
    from xrf_explorer.server.file_system.helper import get_config, set_config

    LOG.info("Finished loading XRF-Explorer")

    # set up configuration
    if not set_config(args.config):
        LOG.critical(
            "Could not find config specified at %s, exiting", args.config)
        exit(-1)

    # serve XRF-Explorer
    config: dict = get_config()
    serve(app, host=config["bind-address"], port=config["port"], max_request_body_size=1073741824000000,
          max_request_header_size=85899345920000)
