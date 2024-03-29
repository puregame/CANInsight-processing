from contextlib import contextmanager

from sqlalchemy import engine_from_config
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from database.models import Base
from config import DATABASE_CONFIG
print(DATABASE_CONFIG)
ENGINE = engine_from_config(DATABASE_CONFIG)

# from alembic import command as alembic_command
# from alembic.config import Config as AlembicConfig

# alembic_command.upgrade(AlembicConfig("database/alembic.ini"), 'head')

@contextmanager
def db_session():
    """ Create a scoped database session. """
    session = scoped_session(sessionmaker(bind=ENGINE, autocommit=False, autoflush=True))
    try:
        yield session
    finally:
        session.remove()