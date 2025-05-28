from sqlalchemy import Column, Integer, String, Float
from backend.config.config import Base  # או מאיפה שאתה מייבא את Base
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country = Column(String)
    lat = Column(Float)
    lon = Column(Float)
