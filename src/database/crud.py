# crud.py
from re import L
from typing import Optional


from database import Session, ENGINE
from database.models import *

from sqlalchemy import desc, asc

def new_vehicle(unit_number, vehicle_type="unknown", serial_number=None, status=None):
    s = Session(bind=ENGINE)
    b = Vehicle(unit_number=unit_number, vehicle_type=vehicle_type, serial_number=serial_number, status=status)
    s.add(b)
    s.commit()
    s.close()

def get_vehicles():
    s = Session(bind=ENGINE)
    q = s.query(Vehicle).all()
    s.close()
    return q

def get_vehicle_by_unit_number(unit_number) -> Vehicle:
    s = Session(bind=ENGINE)
    q = s.query(Vehicle).filter(Vehicle.unit_number==unit_number).first()
    s.close()
    return q

def get_logs_for_unit(unit_number, page=None, per_page=None, hidden=False) -> tuple[list[LogFile], bool]:
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(
        LogFile.unit_number == unit_number,
        LogFile.hide_in_web == hidden
    ).order_by(asc(LogFile.upload_time))
    if page is not None and per_page is not None:
        q = q.offset((page - 1) * per_page).limit(per_page + 1)
    result = q.all()
    s.close()
    has_next = len(result) > per_page
    logs = result[:per_page]
    return result, has_next

from datetime import datetime
from sqlalchemy.orm import Session
from database.models import LogFile
import uuid

def new_log_file(
    log_start_time: datetime,
    unit_number: str,
    status: str = "Uploaded",
    hash: bytes = None,
    upload_time: datetime = None,
    length_sec: float = None,
    samples: int = None,
    original_file_name: str = "",
    uuid_input: str = None  # Add uuid as an optional argument
) -> LogFile:
    s = Session(bind=ENGINE)

    if upload_time is None:
        upload_time = datetime.now()

    # Get next available log_number for this unit
    last_log = (
        s.query(LogFile)
        .filter_by(unit_number=unit_number)
        .order_by(LogFile.log_number.desc())
        .first()
    )
    next_log_number = (last_log.log_number + 1) if last_log else 1

    # Use provided uuid if present, otherwise generate a new one
    log_id = uuid_input if uuid_input is not None else str(uuid.uuid4())

    # Create new log
    log = LogFile(
        id=log_id,
        log_start_time=log_start_time,
        upload_time=upload_time,
        unit_number=unit_number,
        log_number=next_log_number,
        length_sec=length_sec,
        samples=samples,
        processing_status=status,
        hash=hash,
        original_file_name=original_file_name,
        file_stem=f"{unit_number}_{next_log_number:05d}"
    )

    s.add(log)
    s.commit()
    log_num = log.log_number
    s.close()
    return log


def update_log_file_status(id,processing_status):
    s = Session(bind=ENGINE)
    s.query(LogFile).filter(LogFile.id==id).update({"processing_status": processing_status})
    s.commit()
    s.close()

def update_log_end_time(id, end_time: datetime):
    s = Session(bind=ENGINE)
    s.query(LogFile).filter(LogFile.id==id).update({"log_end_time": end_time})
    s.commit()
    s.close()

def update_log_file_len(id, duration, samples):
    s = Session(bind=ENGINE)
    s.query(LogFile).filter(LogFile.id==id).update({"length_sec": duration, "samples": samples})
    s.commit()
    s.close()

def get_log_file(start_time: datetime, unit_number: str) -> Optional[LogFile]:
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.log_start_time==start_time).first()
    s.close()
    return q

def get_log_file(uuid:str) -> Optional[LogFile]:
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.id==uuid).first()
    s.close()
    return q

def hide_show_log_file(id, hidden=True):
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.id==id).update({"hide_in_web": hidden})
    s.commit()
    s.close()
    return q


def update_log_file_headline(id, headline):
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.id==id).update({"headline": headline})
    s.commit()
    s.close()
    return q

def get_visible_logs_for_unit(unit_number):
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.hide_in_web==False).order_by(desc(LogFile.upload_time)).all()
    s.close()
    return q

def get_all_logs_for_unit(unit_number):
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number).all()
    s.close()
    return q

def get_comments_for_log(id):
    s = Session(bind=ENGINE)
    q = s.query(LogComment).filter(LogComment.log_id ==id).all()
    s.close()
    return q

def delete_log_file(id):
    s = Session(bind=ENGINE)
    s.query(LogFile).filter(LogFile.id==id).delete()
    s.commit()
    s.close()

def does_log_exist(hash: bytes, unit_number: str) -> Boolean:
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.hash==hash).first()
    s.close()
    if q is None:
        return False
    else:
        return True
    
def get_log_with_hash(hash: bytes, unit_number: str) -> LogFile:
    s = Session(bind=ENGINE)
    q = s.query(LogFile).filter(LogFile.unit_number==unit_number, LogFile.hash==hash).first()
    s.close()
    return q


def create_log_in_database(log_start_time: datetime, unit_number: str, hash: bytes, unit_type:str="", original_file_name:str="", provided_uuid=None) -> LogFile:
    if get_vehicle_by_unit_number(unit_number) is None:
        # If the vehicle does not exist, create it
        new_vehicle(unit_number, unit_type)
    return new_log_file(log_start_time, unit_number, status="Uploaded",original_file_name=original_file_name, upload_time=datetime.now(), hash=hash, uuid_input=provided_uuid)

def get_log_status(id) -> Optional[str]:
    s = Session(bind=ENGINE)
    q = s.query(LogFile.processing_status).filter(LogFile.id==id).first()
    s.close()
    return q[0]

def is_log_status(id, status_to_check):
    return (get_log_status(id) == status_to_check)

def new_log_comment(log_id, comment, timestamp):
    s = Session(bind=ENGINE)
    comment = LogComment(log_id = log_id,
                        timestamp=timestamp,
                        comment=comment)
    s.add(comment)
    s.commit()
    comment_id = comment.id
    s.close()
    return comment_id

def delete_log_comment(comment_id):
    s = Session(bind=ENGINE)
    s.query(LogComment).filter(LogComment.id == comment_id).delete()
    s.commit()
    s.close()