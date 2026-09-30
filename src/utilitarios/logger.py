import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def get_logger(name=__name__, log_dir="logs", log_file="catalog_integration.log"):
    os.makedirs(log_dir, exist_ok=True)
    log_path=os.path.join(log_dir, log_file)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    fh = RotatingFileHandler(log_path, maxBytes=5242880, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    return logger

logger = get_logger("catalog_integration")
