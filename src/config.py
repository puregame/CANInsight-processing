
import os
from pathlib import Path


DATA_FOLDER = Path("./can_data/")
DATA_FOLDER.mkdir(parents=True, exist_ok=True)

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()

if DB_BACKEND == "postgres":
    # Default to PostgreSQL
    database_url_params = {
        'username': 'root',
        'password': 'root',
        'hostname': 'localhost',
        'port': 5432,
        'database': 'logserver_db'
    }

    for k in database_url_params:
        try:
            env_key = f"DB_{k.upper()}"
            database_url_params[k] = os.environ[env_key]
        except KeyError:
            # Keep default if env var not set
            pass

    DATABASE_CONFIG = {
        'sqlalchemy.url': 'postgresql://{username}:{password}@{hostname}:{port}/{database}'.format(**database_url_params)
    }
else:
    # Use SQLite DB in the data folder
    sqlite_path = DATA_FOLDER / "logserver_db.sqlite3"
    DATABASE_CONFIG = {
        'sqlalchemy.url': f"sqlite:///{sqlite_path}"
    }