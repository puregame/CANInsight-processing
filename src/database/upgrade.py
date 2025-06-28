from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import os

from config import DATABASE_CONFIG

def init_and_upgrade_db():
    """ Initialize and/or upgrade database schema. """
    db_url = DATABASE_CONFIG['sqlalchemy.url']
    engine = create_engine(db_url, future=True)
    
    # Create DB file if using SQLite (the engine handles this implicitly)
    if db_url.startswith("sqlite:///"):
        # Optional: manually create tables if Alembic isn't used
        from database.models import Base  # Adjust to match your model import
        Base.metadata.create_all(engine)
        return

    # PostgreSQL: run Alembic migrations
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), 'alembic.ini'))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")