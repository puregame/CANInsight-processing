from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import os

from . import ENGINE

from config import DATABASE_CONFIG

def init_and_upgrade_db():
    """ Initialize and/or upgrade database schema. """
    
    # Create DB file if using SQLite (the engine handles this implicitly)
    if DATABASE_CONFIG['sqlalchemy.url'].startswith("sqlite:///"):
        # if we are using sqlite then do not use alembic and base create them all
        from database.models import Base  # Adjust to match your model import
        Base.metadata.create_all(ENGINE)
        return

    # PostgreSQL: run Alembic migrations
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), 'alembic.ini'))
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_CONFIG['sqlalchemy.url'])
    command.upgrade(alembic_cfg, "head")