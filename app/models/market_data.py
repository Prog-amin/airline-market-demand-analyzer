""
Market Data database model.
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Float, Integer, Date, ForeignKey, Boolean, Index, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class MarketData(Base):
    """MarketData model representing aggregated market demand data."""
    __tablename__ = "market_data"
    
    # Route information
    origin_airport_id = Column(Integer, ForeignKey('airports.id'), nullable=False, index=True)
    destination_airport_id = Column(Integer, ForeignKey('airports.id'), nullable=False, index=True)
    
    # Date information
    data_date = Column(Date, nullable=False, index=True)  # The date this data point represents
    collection_date = Column(Date, nullable=False, default=date.today)  # When this data was collected
    
    # Demand metrics
    search_volume = Column(Integer, nullable=True)  # Number of searches for this route
    booking_count = Column(Integer, nullable=True)  # Number of actual bookings
    average_price = Column(Numeric(10, 2), nullable=True)  # Average price for this route
    min_price = Column(Numeric(10, 2), nullable=True)  # Minimum price found
    max_price = Column(Numeric(10, 2), nullable=True)  # Maximum price found
    
    # Availability metrics
    available_seats = Column(Integer, nullable=True)  # Total available seats
    flight_count = Column(Integer, nullable=True)  # Number of flights on this route
    
    # Load factor (percentage of seats filled)
    load_factor = Column(Float, nullable=True)  # Calculated as (booked_seats / available_seats) * 100
    
    # Historical comparison
    price_change_7d = Column(Float, nullable=True)  # Price change percentage over 7 days
    price_change_30d = Column(Float, nullable=True)  # Price change percentage over 30 days
    
    # Additional metadata
    data_source = Column(String(50), nullable=False)  # Source of this data (e.g., 'amadeus', 'mock')
    is_estimated = Column(Boolean, default=False, nullable=False)  # Whether this is estimated data
    
    # Raw data from source (if any)
    raw_data = Column(JSONB, nullable=True)
    
    # Relationships
    origin_airport = relationship("Airport", foreign_keys=[origin_airport_id], backref="origin_market_data")
    destination_airport = relationship("Airport", foreign_keys=[destination_airport_id], backref="destination_market_data")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_market_data_date', 'data_date'),
        Index('idx_market_data_route_date', 'origin_airport_id', 'destination_airport_id', 'data_date'),
        Index('idx_market_data_collection_date', 'collection_date'),
    )
    
    def __repr__(self):
        return f"<MarketData {self.origin_airport_id}-{self.destination_airport_id} on {self.data_date}>"
