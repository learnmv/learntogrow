from sqlalchemy import Column, Integer, String, Text, ARRAY, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base


class GeoGebra(Base):
    """GeoGebra applet command templates from database."""

    __tablename__ = "geogebra"

    id = Column(Integer, primary_key=True)
    applet_type = Column(String(20), unique=True, nullable=False)
    valid_command_template = Column(ARRAY(Text), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
