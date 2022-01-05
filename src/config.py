
import os
from pathlib import Path

DATA_FOLDER = Path("/data")
DATA_FOLDER.mkdir(parents=True, exist_ok=True)


DATABASE_CONFIG = {'sqlalchemy.url': 'postgresql://root:root@database:5432/logserver_db'}
# DATABASE_CONFIG['sqlalchemy.url'] = DATABASE_CONFIG.pop('url').format(os.environ['DB_PASSWORD'])