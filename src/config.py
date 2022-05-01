
import os
from pathlib import Path

DATA_FOLDER = Path("/data")
DATA_FOLDER.mkdir(parents=True, exist_ok=True)

database_url_params = {'username': 'root',
                        'password': 'root',
                        'hostname': 'database',
                        'port': 5432,
                        'database': 'logserver_db'}
for k in database_url_params:
    try:
        environ_key = "DB_{}".format(k.upper())
        database_url_params[k] = os.environ(environ_key)
    except KeyError:
        # ignore environment variable key not found errors
        pass

DATABASE_CONFIG = {'sqlalchemy.url': 'postgresql://{username}:{password}@{hostname}:{port}/{database}'.format(database_url_params)
