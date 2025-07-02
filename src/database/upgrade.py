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
        # Optional: manually create tables if Alembic isn't used
        from database.models import Base  # Adjust to match your model import
        Base.metadata.create_all(ENGINE)
        return

    # PostgreSQL: run Alembic migrations
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), 'alembic.ini'))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")