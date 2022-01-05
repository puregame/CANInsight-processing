
import os

DATABASE_CONFIG = {'url': 'postgresql://batterydb_user:Tracks123@10.11.0.117:5432/logserver_db'}
# DATABASE_CONFIG['sqlalchemy.url'] = DATABASE_CONFIG.pop('url').format(os.environ['DB_PASSWORD'])