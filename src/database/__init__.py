#__init__.py
from contextlib import contextmanager

from sqlalchemy import engine_from_config
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from config import DATABASE_CONFIG

print("Creating database engine with config:")
print(DATABASE_CONFIG)
ENGINE = engine_from_config(DATABASE_CONFIG)


from database.models import Base  # <- import AFTER Engine is defined
# Bind Base metadata to ENGINE
Base.metadata.bind = ENGINE

Session = scoped_session(sessionmaker(bind=ENGINE))

# 🔍 Assert the bind is working
assert Base.metadata.bind is ENGINE, "Metadata is not bound to engine"


from sqlalchemy import event

# Enable foreign key support for SQLite
if DATABASE_CONFIG['sqlalchemy.url'].startswith("sqlite:///"):
    @event.listens_for(ENGINE, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# @contextmanager
# def db_session():
#     """ Create a scoped database session. """
#     session = scoped_session(sessionmaker(bind=ENGINE, autocommit=False, autoflush=True))
#     try:
#         yield session
#     finally:
#         session.remove()