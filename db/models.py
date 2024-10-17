from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    size = Column(String, nullable=True)
    uri = Column(String, nullable=False)
    img_uri = Column(String, nullable=True)  # None означає, що поле може бути порожнім
    posted_date = Column(DateTime, nullable=False)
    parsed_date = Column(DateTime, nullable=False)
    viewed = Column(Boolean, default=False)