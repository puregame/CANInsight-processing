from sqlalchemy.exc import IntegrityError

from database import db_session
from database.models import Vehicle, LogFile

from database.upgrade import init_and_upgrade_db

init_and_upgrade_db()

# insert testing data

