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
    q = s.query(Vehicle).filter(Vehicle.unit_number==unit_number).first()
    s.close()
    return q

def new_log_file(start_time, unit_number, status="Uploaded", upload_time=None, length=None, samples=None,original_file_name=""):
    s = Session()
    if upload_time is None:
        upload_time=datetime.now()
    log = LogFile(start_time=start_time, 
                     upload_time=upload_time, 
                     unit_number=unit_number, 
                     length=length,
                     samples=samples,
                     processing_status=status,
                     original_file_name=original_file_name)
    s.add(log)
    s.commit()
    log_id = log.id
    s.close()
    return log_id

def update_log_file_status(start_time, unit_number, processing_status):
    s = Session()
    s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).update({"processing_status": processing_status})
    s.commit()
    s.close()

def update_log_file_len(start_time, unit_number, duration, samples):
    s = Session()
    s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).update({"length": duration, "samples": samples})
    s.commit()
    s.close()

def get_log_file(start_time, unit_number):
    s = Session()
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).first()
    s.close()
    return q

def delete_log_file(start_time, unit_number):
    s = Session()
    s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).delete()
    s.commit()
    s.close()

def create_log_in_database_if_not_exists(log_start_time, unit_number, unit_type=None, original_file_name=""):
    if get_log_file(log_start_time, unit_number) is not None:
        return # log exists, do nothing
    if get_vehicle_by_unit_number(unit_number) is None:
        new_vehicle(unit_number, unit_type)
    return new_log_file(log_start_time, unit_number, status="Uploaded",original_file_name=original_file_name)

def get_log_status(start_time, unit_number):
    s = Session()
    q = s.query(LogFile.processing_status).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).first()[0]
    s.close()
    return q

def is_log_status(start_time, unit_number, status_to_check):
    return (get_log_status(start_time, unit_number) == status_to_check)