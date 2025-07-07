### models.py ###

from datetime import datetime, timezone
from dateutil import parser

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Date, Float, Integer, DateTime, Boolean, ForeignKey, UniqueConstraint, LargeBinary

import uuid

Base = declarative_base()

from sqlalchemy.types import TypeDecorator, DateTime
from sqlalchemy.dialects.sqlite import DATETIME as SQLiteDateTime
from sqlalchemy import inspect

class TZNaiveDateTime(TypeDecorator):
    impl = DateTime

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        # Parse strings to datetime
        if isinstance(value, str):
            value = parser.isoparse(value)

        # Remove timezone for SQLite
        if isinstance(value, datetime):
            if dialect.name == "sqlite" and value.tzinfo is not None:
                value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        return value

class Vehicle(Base):
    __tablename__ = 'vehicle'
    unit_number = Column(String, primary_key=True, nullable=False)
    vehicle_type = Column(String)
    serial_number = Column(String)
    status = Column(String)

    def __repr__(self):
        return "<Vehicle(unit_number='{}', serial_number='{}', status={})>"\
                .format(self.unit_number, self.serial_number, self.status)

class LogFile(Base):
    __tablename__ = 'log_file'
    __table_args__ = (
        UniqueConstraint('unit_number', 'log_number', name='uq_unit_log_number'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    log_number = Column(Integer, nullable=False)

    log_start_time = Column(TZNaiveDateTime)
    log_end_time = Column(TZNaiveDateTime)
    upload_time = Column(TZNaiveDateTime, default=datetime.now, nullable=False)
    unit_number = Column(String, ForeignKey("vehicle.unit_number",
                                            name='vehicle_id_log_fkey',
                                            onupdate='CASCADE',
                                            ondelete='RESTRICT'), nullable=False)
    hash = Column(LargeBinary(32)) #does not have to be unique, if empty array then will not be unique
    length_sec = Column(Float) #length of log in seconds
    samples = Column(Integer)
    processing_status = Column(String, default="Uploaded")
    original_file_name = Column(String)
    note = Column(String)
    headline = Column(String)
    hide_in_web = Column(Boolean, default=False)

    def __repr__(self):
        return "<LogFile(id='{}', log_start_time='{}', unit_number={}, log_number={}, length_sec={}, samples={}, original_file_name={})>"\
                .format(self.id, self.log_start_time, self.unit_number, self.log_number, self.length_sec, self.samples, self.original_file_name)

class LogComment(Base):
    __tablename__ = "log_comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(36), ForeignKey("log_file.id",
                                        name="comment_log_id_fkey",
                                        onupdate='CASCADE',
                                        ondelete='CASCADE'), nullable=False)
    timestamp = Column(Integer)
    comment = Column(String)

    def __repr__(self):
        return "<LogComment(log_id='{}', timestamp='{}', comment={})>"\
            .format(self.log_id, self.timestamp, self.comment)
