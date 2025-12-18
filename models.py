from sqlalchemy import Column, Integer, String, Text, JSON, Numeric
from database import Base

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)

    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)
    seniority = Column(String, nullable=True)
    job_type = Column(String, nullable=True)
    job_link = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    

