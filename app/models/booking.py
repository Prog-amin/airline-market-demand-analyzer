""
Booking database model.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Index, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base

class Booking(Base):
    """Booking model representing flight bookings in the system."""
    __tablename__ = "bookings"
    
    # Booking identification
    booking_reference = Column(String(10), unique=True, nullable=False, index=True)
    
    # Flight information
    flight_id = Column(Integer, ForeignKey('flights.id'), nullable=False, index=True)
    
    # Passenger information
    passenger_name = Column(String(255), nullable=False)
    passenger_email = Column(String(255), nullable=False)
    passenger_phone = Column(String(50), nullable=True)
    
    # Booking details
    booking_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    travel_date = Column(DateTime, nullable=False, index=True)
    seat_number = Column(String(10), nullable=True)
    booking_class = Column(String(10), nullable=False)  # Economy, Business, First, etc.
    
    # Pricing
    base_fare = Column(Numeric(10, 2), nullable=False)
    taxes = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='AUD', nullable=False)
    
    # Payment information
    payment_status = Column(String(20), default='pending', nullable=False)  # pending, paid, cancelled, refunded
    payment_reference = Column(String(100), nullable=True)
    payment_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), default='confirmed', nullable=False)  # confirmed, cancelled, used, no-show
    
    # Additional metadata
    special_requests = Column(String(500), nullable=True)
    notes = Column(String(1000), nullable=True)
    
    # Raw data from source (if any)
    raw_data = Column(JSONB, nullable=True)
    
    # Relationships
    flight = relationship("Flight", backref="bookings")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_booking_reference', 'booking_reference'),
        Index('idx_booking_passenger', 'passenger_email'),
        Index('idx_booking_status', 'status'),
        Index('idx_booking_travel_date', 'travel_date'),
    )
    
    def __init__(self, **kwargs):
        # Generate a unique booking reference if not provided
        if 'booking_reference' not in kwargs:
            kwargs['booking_reference'] = self._generate_booking_reference()
        super().__init__(**kwargs)
    
    def _generate_booking_reference(self):
        """Generate a unique booking reference."""
        # Generate a 6-character alphanumeric code
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def __repr__(self):
        return f"<Booking {self.booking_reference} - {self.passenger_name} on {self.travel_date}>"
