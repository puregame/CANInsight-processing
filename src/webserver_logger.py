
import logging
from logging.handlers import RotatingFileHandler

from config import DATA_FOLDER

formatter = logging.Formatter(
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s: %(message)s")
logger = logging.getLogger('web_api')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('web1.log', maxBytes=1000000, backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)