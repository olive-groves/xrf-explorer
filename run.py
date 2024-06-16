import logging
import argparse

from datetime import datetime
from os import environ
from sys import stdout

LOG: logging.Logger = logging.getLogger(__name__)

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

    # set logging output handler
    outputHandler: logging.Handler = logging.StreamHandler(stdout)  # if environment variable is not set, use stdout
    mode: str | None = environ.get("XRF_EXPLORER_LOG_MODE")
    if mode == "PROD":
        currentTime: str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        outputHandler = logging.FileHandler(f"logs/log_{currentTime}.log")

    # set up logger
    logging.basicConfig(
        level=loglevel,  # lowest logging level used
        format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
        handlers=[outputHandler]  # set output handler
    )

    LOG.info("Starting XRF-Explorer")
    # import app dependencies only after showing initial log message
    from waitress import serve
    from xrf_explorer import app
    from xrf_explorer.server.file_system.config_handler import get_config, set_config

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
