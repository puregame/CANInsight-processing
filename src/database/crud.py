from database.models import *

from config import DATABASE_CONFIG
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# sqlalchemy stuff 

print("create engine")
engine = create_engine(DATABASE_CONFIG['sqlalchemy.url'])
Session = sessionmaker(bind=engine)

def new_vehicle(unit_number, vehicle_type, serial_number=None, status=None):
    s = Session()
    b = Vehicle(unit_number=unit_number, vehicle_type=vehicle_type, serial_number=serial_number, status=status)
    s.add(b)
    s.commit()
    s.close()

def get_vehicle_by_unit_number(unit_number):
    s = Session()
    return s.query(Vehicle).filter(Vehicle.unit_number==unit_number).first()

def new_log_file(start_time, unit_number, status="Uploaded", upload_time=datetime.now(), length=None, samples=None):
    s = Session()
    log = LogFile(start_time=start_time, 
                     upload_time=upload_time, 
                     unit_number=unit_number, 
                     length=length,
                     samples=samples,
                     processing_status=status)
    s.add(log)
    s.commit()
    log_id = log.id
    print("Log ID: {}".format(log_id))
    s.close()
    return log_id

def get_log_file(start_time, unit_number):
    s = Session()
    return s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).first()

def delete_log_file(start_time, unit_number):
    s = Session()
    s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).delete()

