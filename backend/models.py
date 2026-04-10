from sqlalchemy import create_engine, Column, String, Date, DateTime, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///attendance.db", echo=False)
Session = sessionmaker(bind=engine)

class Student(Base):
    __tablename__ = "students"
    id       = Column(String, primary_key=True)   # e.g. "STU001"
    name     = Column(String, nullable=False)
    class_   = Column(String)
    enrolled = Column(DateTime, default=datetime.now)

class Attendance(Base):
    __tablename__ = "attendance"
    id         = Column(String, primary_key=True)  # "STU001_2024-01-15"
    student_id = Column(String, nullable=False)
    date       = Column(Date, nullable=False)
    status     = Column(Enum("present", "absent", name="status"), default="absent")
    timestamp  = Column(DateTime, nullable=True)

def init_db():
    Base.metadata.create_all(engine)