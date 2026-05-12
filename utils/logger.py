import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')


def get_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR


def setup_logger():
    log_dir = get_log_dir()
    log_filename = datetime.now().strftime('%Y%m%d_%H%M%S') + '.log'
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger('QingFengBot')
    logger.setLevel(logging.DEBUG)

    fh = RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=30, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = setup_logger()
