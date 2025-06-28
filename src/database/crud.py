from re import L
from typing import Optional

from database.models import *

from config import DATABASE_CONFIG
from sqlalchemy import create_engine, desc
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

def get_vehicles():
    s = Session()
    q = s.query(Vehicle).all()
    s.close()
    return q

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

def hide_log_file(log_id):
    s = Session()
    q = s.query(LogFile).filter(LogFile.id==log_id).update({"hide_in_web": True})
    s.commit()
    s.close()
    return q


def update_log_file_headline(log_id, headline):
    s = Session()
    q = s.query(LogFile).filter(LogFile.id==log_id).update({"headline": headline})
    s.commit()
    s.close()
    return q

def get_logs_for_unit(unit_number):
    s = Session()
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.hide_in_web==False).order_by(desc(LogFile.upload_time)).all()
    s.close()
    return q

def get_all_logs_for_unit(unit_number):
    s = Session()
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number).all()
    s.close()
    return q

def get_comments_for_log(log_id):
    s = Session()
    q = s.query(LogComment).filter(LogComment.log_id ==log_id).all()
    s.close()
    return q

def delete_log_file(start_time, unit_number):
    s = Session()
    s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.start_time==start_time).delete()
    s.commit()
    s.close()

def does_log_exist(log_start_time: datetime, unit_number: str) -> Boolean:
    existing_log = get_log_file(log_start_time, unit_number)
    if existing_log is None:
        return False
    else:
        return True


def create_log_in_database_if_not_exists(log_start_time: datetime, unit_number: str, unit_type:str="", original_file_name:str=""):
    
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

def new_log_comment(log_id, comment, timestamp):
    s = Session()
    comment = LogComment(log_id = log_id,
                        timestamp=timestamp,
                        comment=comment)
    s.add(comment)
    s.commit()
    comment_id = comment.id
    s.close()
    return comment_id

def delete_log_comment(comment_id):
    s = Session()
    s.query(LogComment).filter(LogComment.id == comment_id).delete()
    s.commit()
    s.close()