### models.py ###

from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Date, Float, Integer, DateTime, Boolean, ForeignKey, UniqueConstraint

Base = declarative_base()

class Vehicle(Base):
    __tablename__ = 'vehicle'
    unit_number = Column(String, primary_key=True)
    vehicle_type = Column(String)
    serial_number = Column(String)
    status = Column(String)

    def __repr__(self):
        return "<Vehicle(unit_number='{}', serial_number='{}', status={})>"\
                .format(self.unit_number, self.serial_number, self.status)

class LogFile(Base):
    __tablename__ = 'log_file'
    __table_args__ = (UniqueConstraint('start_time', 'unit_number', name='_start_unit_unique_constraint'), )
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime)
    upload_time = Column(DateTime, default=datetime.now, nullable=False)
    unit_number = Column(String, ForeignKey("vehicle.unit_number",
                                            name='vehicle_id_log_fkey',
                                            onupdate='CASCADE',
                                            ondelete='RESTRICT'), nullable=False)
    length = Column(Float) #length of log in seconds
    samples = Column(Integer)
    processing_status = Column(String, default="Uploaded")
    original_file_name = Column(String)
    note = Column(String)
    headline = Column(String)
    hide_in_web = Column(Boolean, default=False)

    def __repr__(self):
        return "<LogFile(id='{}', start_time='{}', unit_number={}, length_time={}, samples={}, original_file_name={})>"\
                .format(self.id, self.start_time, self.unit_number, self.length, self.samples, self.original_file_name)

class LogComment(Base):
    __tablename__ = "log_comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(Integer, ForeignKey("log_file.id",
                                        name="comment_log_id_fkey",
                                        onupdate='CASCADE',
                                        ondelete='CASCADE'), nullable=False)
    timestamp = Column(Integer)
    comment = Column(String)

    def __repr__(self):
        return "<LogComment(log_id='{}', timestamp='{}', comment={})>"\
            .format(self.log_id, self.timestamp, self.comment)
