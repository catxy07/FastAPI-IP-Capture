from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, text
from db import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    ip_address = Column(String(45), nullable=True)
    time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    time = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
