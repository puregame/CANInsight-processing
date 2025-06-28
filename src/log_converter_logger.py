import logging
from logging.handlers import RotatingFileHandler
from config import DATA_FOLDER

LOG_PATH = DATA_FOLDER / 'can_processing.log'
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create a custom formatter
formatter = logging.Formatter(
    "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s: %(message)s")

# Create the logger
logger = logging.getLogger('log_converter')
logger.setLevel(logging.DEBUG)

# Avoid adding handlers multiple times in REPL/test environments
if not logger.hasHandlers():
    # File handler (rotating)
    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Console handler (stream)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # You can change to DEBUG if desired
    logger.addHandler(console_handler)
