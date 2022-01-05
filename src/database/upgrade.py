from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig

def init_and_upgrade_db():
    """ Initialize and/or upgrade database schema. """
    alembic_command.upgrade(AlembicConfig("database/alembic.ini"), 'head')