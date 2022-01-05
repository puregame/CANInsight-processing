### models.py ###

from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Date, Float, Integer, DateTime, Boolean, ForeignKey

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

    def __repr__(self):
        return "<LogFile(id='{}', start_time='{}', unit_number={}, length_time={}, samples={})>"\
                .format(self.id, self.start_time, self.unit_number, self.length_time, self.samples)
