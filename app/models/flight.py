""
Flight database model.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Flight(Base):
    """Flight model representing flight data in the system."""
    __tablename__ = "flights"
    
    # Flight identification
    flight_number = Column(String(20), nullable=False)
    airline_iata = Column(String(3), nullable=False)
    airline_icao = Column(String(4), nullable=True)
    
    # Route information
    origin_airport_id = Column(Integer, ForeignKey('airports.id'), nullable=False, index=True)
    destination_airport_id = Column(Integer, ForeignKey('airports.id'), nullable=False, index=True)
    
    # Flight schedule
    departure_time = Column(DateTime, nullable=False, index=True)
    arrival_time = Column(DateTime, nullable=False, index=True)
    
    # Pricing and availability
    price = Column(Float, nullable=True)  # in AUD
    currency = Column(String(3), default='AUD', nullable=False)
    available_seats = Column(Integer, nullable=True)
    
    # Flight status
    status = Column(String(20), nullable=False, default='scheduled')  # scheduled, active, landed, cancelled, etc.
    is_direct = Column(Boolean, default=True, nullable=False)
    
    # Aircraft information
    aircraft_type = Column(String(10), nullable=True)
    aircraft_registration = Column(String(20), nullable=True)
    
    # Additional metadata
    data_source = Column(String(50), nullable=False)  # e.g., 'amadeus', 'mock', 'aviationstack'
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Raw data from source (if any)
    raw_data = Column(JSONB, nullable=True)
    
    # Relationships
    origin_airport = relationship("Airport", foreign_keys=[origin_airport_id], backref="departing_flights")
    destination_airport = relationship("Airport", foreign_keys=[destination_airport_id], backref="arriving_flights")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_flight_departure', 'departure_time'),
        Index('idx_flight_route', 'origin_airport_id', 'destination_airport_id'),
        Index('idx_flight_airline', 'airline_iata'),
    )
    
    def __repr__(self):
        return f"<Flight {self.airline_iata}{self.flight_number} from {self.origin_airport_id} to {self.destination_airport_id} at {self.departure_time}>"
