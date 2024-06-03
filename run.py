import logging
import argparse

LOG: logging.Logger = logging.getLogger(__name__)

parser: argparse.ArgumentParser = argparse.ArgumentParser(prog="python run.py", description="XRF-Explorer")
parser.add_argument("-c", "--config", dest="config", default="config/backend.yml", metavar="PATH",
                    help="path to the XRF-Explorer configuration file")
parser.add_argument("-l", "--log", dest="loglevel", default="INFO", metavar="LEVEL",
                    help="set logging level, can be any of CRITICAL, ERROR, WARN, INFO, DEBUG")

if __name__ == '__main__':
    # read commandline arguments
    args = parser.parse_args()

    # get logging level
    loglevel = logging.getLevelName(args.loglevel)

    # set up logger
    logging.basicConfig(
        level=loglevel,  # lowest logging level used
        # filename="logs/log.log",        # path to log file to output instead of console
        # filemode="w",                   # access mdoe to file specified in `filename`
        format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
    )

    LOG.info("Starting XRF-Explorer")

    # import app dependencies only after showing initial log message
    from waitress import serve
    from xrf_explorer import app
    from xrf_explorer.server.file_system.config_handler import load_yml

    LOG.info("Finished loading XRF-Explorer")

    # load config
    config: dict = load_yml(args.config)

    # serve XRF-Explorer
    serve(app, host=config["bind-address"], port=config["port"], max_request_body_size=1073741824000000,
          max_request_header_size=85899345920000)
