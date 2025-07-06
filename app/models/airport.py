""
Airport database model.
"""
from sqlalchemy import Column, String, Float, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base_class import Base

class Airport(Base):
    """Airport model representing airports in the system."""
    __tablename__ = "airports"
    
    # Core airport information
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    icao_code = Column(String(4), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    
    # Location data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=True)
    
    # Additional metadata
    timezone_offset = Column(Integer, nullable=True)  # in hours from UTC
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Raw data from source (if any)
    raw_data = Column(JSONB, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_airport_city', 'city'),
        Index('idx_airport_country', 'country'),
        Index('idx_airport_coordinates', 'latitude', 'longitude'),
    )
    
    def __repr__(self):
        return f"<Airport {self.iata_code} - {self.name}, {self.city}, {self.country}>"
