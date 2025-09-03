from sqlalchemy.exc import IntegrityError

from database.upgrade import init_and_upgrade_db

init_and_upgrade_db()
