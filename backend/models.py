from sqlalchemy import create_engine, Column, String, Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///attendance.db", echo=False)
Session = sessionmaker(bind=engine)


class Student(Base):
    __tablename__ = "students"

    id       = Column(String, primary_key=True)   # e.g. "STU001"
    name     = Column(String, nullable=False)
    class_   = Column(String, default="")
    enrolled = Column(DateTime, default=datetime.now)


class Attendance(Base):
    __tablename__ = "attendance"

    # Composite primary key — no more string concat issues
    student_id = Column(String, ForeignKey("students.id"), primary_key=True)
    date       = Column(Date, primary_key=True)
    status     = Column(Enum("present", "absent", name="att_status"), default="absent")
    timestamp  = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(engine)