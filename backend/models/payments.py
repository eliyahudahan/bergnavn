from sqlalchemy import Column, Integer
from backend.config.config import Base  # או הנתיב הנכון אל Base אצלך

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
