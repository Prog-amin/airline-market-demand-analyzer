"""
Mock data provider for airline market data.

This module provides mock data for development and testing purposes.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

# Australian airports with IATA codes and coordinates
AUSTRALIAN_AIRPORTS = [
    {"iata": "SYD", "name": "Sydney Airport", "city": "Sydney", "country": "Australia", 
     "lat": -33.9399, "lon": 151.1753, "timezone": "Australia/Sydney"},
    {"iata": "MEL", "name": "Melbourne Airport", "city": "Melbourne", "country": "Australia",
     "lat": -37.6696, "lon": 144.8498, "timezone": "Australia/Melbourne"},
    {"iata": "BNE", "name": "Brisbane Airport", "city": "Brisbane", "country": "Australia",
     "lat": -27.3940, "lon": 153.1219, "timezone": "Australia/Brisbane"},
    {"iata": "PER", "name": "Perth Airport", "city": "Perth", "country": "Australia",
     "lat": -31.9522, "lon": 115.8589, "timezone": "Australia/Perth"},
    {"iata": "ADL", "name": "Adelaide Airport", "city": "Adelaide", "country": "Australia",
     "lat": -34.9285, "lon": 138.6007, "timezone": "Australia/Adelaide"},
    {"iata": "CBR", "name": "Canberra Airport", "city": "Canberra", "country": "Australia",
     "lat": -35.3069, "lon": 149.1950, "timezone": "Australia/Sydney"},
    {"iata": "HBA", "name": "Hobart Airport", "city": "Hobart", "country": "Australia",
     "lat": -42.8361, "lon": 147.5103, "timezone": "Australia/Hobart"},
    {"iata": "DRW", "name": "Darwin Airport", "city": "Darwin", "country": "Australia",
     "lat": -12.4083, "lon": 130.8727, "timezone": "Australia/Darwin"},
    {"iata": "CNS", "name": "Cairns Airport", "city": "Cairns", "country": "Australia",
     "lat": -16.8858, "lon": 145.7553, "timezone": "Australia/Brisbane"},
    {"iata": "OOL", "name": "Gold Coast Airport", "city": "Gold Coast", "country": "Australia",
     "lat": -28.1667, "lon": 153.5000, "timezone": "Australia/Brisbane"},
]

# Major airlines operating in Australia
AIRLINES = [
    {"iata": "QF", "name": "Qantas"},
    {"iata": "VA", "name": "Virgin Australia"},
    {"iata": "JQ", "name": "Jetstar"},
    {"iata": "TT", "name": "Tigerair Australia"},
    {"iata": "NZ", "name": "Air New Zealand"},
    {"iata": "EY", "name": "Etihad Airways"},
    {"iata": "SQ", "name": "Singapore Airlines"},
    {"iata": "CX", "name": "Cathay Pacific"},
    {"iata": "EK", "name": "Emirates"},
    {"iata": "LA", "name": "LATAM"},
]

# Aircraft types with capacity ranges
AIRCRAFT_TYPES = [
    {"code": "A320", "name": "Airbus A320", "capacity": (150, 186)},
    {"code": "A330", "name": "Airbus A330", "capacity": (250, 300)},
    {"code": "A350", "name": "Airbus A350", "capacity": (300, 350)},
    {"code": "A380", "name": "Airbus A380", "capacity": (500, 853)},
    {"code": "B737", "name": "Boeing 737", "capacity": (130, 215)},
    {"code": "B747", "name": "Boeing 747", "capacity": (366, 416)},
    {"code": "B777", "name": "Boeing 777", "capacity": (301, 550)},
    {"code": "B787", "name": "Boeing 787", "capacity": (242, 330)},
]

class MockDataProvider:
    """Provides mock data for the airline market analysis application."""
    
    @staticmethod
    def get_airports() -> List[Dict[str, Any]]:
        """Get a list of Australian airports.
        
        Returns:
            List of airport dictionaries with IATA code, name, and location data.
        """
        return AUSTRALIAN_AIRPORTS
    
    @staticmethod
    def get_flights(
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Generate mock flight data.
        
        Args:
            origin: IATA code of origin airport (optional)
            destination: IATA code of destination airport (optional)
            date_from: Start date for flights (default: today)
            date_to: End date for flights (default: today + 30 days)
            limit: Maximum number of flights to return
            
        Returns:
            List of flight dictionaries with flight details.
        """
        # Set default date range if not provided
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        date_from = date_from or today
        date_to = date_to or (today + timedelta(days=30))
        
        # Filter airports if origin/destination specified
        airports = AUSTRALIAN_AIRPORTS.copy()
        origin_airport = next((a for a in airports if a["iata"] == origin), None) if origin else None
        dest_airport = next((a for a in airports if a["iata"] == destination), None) if destination else None
        
        # If origin/destination not found, pick random ones
        if not origin_airport:
            origin_airport = random.choice(airports)
        if not dest_airport:
            dest_airport = random.choice([a for a in airports if a["iata"] != origin_airport["iata"]])
        
        flights = []
        current_date = date_from
        
        # Generate flights for each day in the date range
        while current_date <= date_to and len(flights) < limit:
            # Generate 1-5 flights per day
            for _ in range(random.randint(1, 5)):
                if len(flights) >= limit:
                    break
                    
                # Generate random departure time (between 6 AM and 10 PM)
                departure_time = current_date.replace(
                    hour=random.randint(6, 22),
                    minute=random.choice([0, 15, 30, 45]),
                    second=0,
                    microsecond=0
                )
                
                # Generate random flight duration (1-6 hours)
                duration_hours = random.randint(1, 6)
                duration = timedelta(hours=duration_hours, minutes=random.randint(0, 59))
                arrival_time = departure_time + duration
                
                # Select random airline and aircraft
                airline = random.choice(AIRLINES)
                aircraft = random.choice(AIRCRAFT_TYPES)
                capacity = random.randint(*aircraft["capacity"])
                booked = random.randint(int(capacity * 0.5), int(capacity * 0.9))  # 50-90% booked
                
                # Generate random price (base price + distance factor + demand factor)
                base_price = random.uniform(100, 300)
                distance = random.uniform(500, 4000)  # Random distance in km
                price = round(base_price + (distance * 0.1) + (random.uniform(-50, 100)), 2)
                
                flight_data = {
                    "id": str(uuid.uuid4()),
                    "flight_number": f"{airline['iata']}{random.randint(100, 9999)}",
                    "airline": airline,
                    "origin": origin_airport,
                    "destination": dest_airport,
                    "departure_time": departure_time.isoformat(),
                    "arrival_time": arrival_time.isoformat(),
                    "duration": int(duration.total_seconds() / 60),  # in minutes
                    "aircraft": aircraft,
                    "capacity": capacity,
                    "booked_seats": booked,
                    "available_seats": capacity - booked,
                    "load_factor": round((booked / capacity) * 100, 1),
                    "price": price,
                    "currency": "AUD",
                    "status": random.choices(
                        ["scheduled", "delayed", "cancelled"],
                        weights=[0.9, 0.08, 0.02],
                        k=1
                    )[0],
                    "stops": random.choices([0, 1, 2], weights=[0.7, 0.25, 0.05], k=1)[0],
                    "data_source": "mock"
                }
                
                flights.append(flight_data)
            
            current_date += timedelta(days=1)
        
        return flights
    
    @staticmethod
    def get_market_data(
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Generate mock market data for analysis.
        
        Args:
            origin: IATA code of origin airport (optional)
            destination: IATA code of destination airport (optional)
            days: Number of days of historical data to generate
            
        Returns:
            List of market data points with demand and pricing information.
        """
        # Filter airports if origin/destination specified
        airports = AUSTRALIAN_AIRPORTS.copy()
        origin_airport = next((a for a in airports if a["iata"] == origin), None) if origin else None
        dest_airport = next((a for a in airports if a["iata"] == destination), None) if destination else None
        
        # If origin/destination not found, pick random ones
        if not origin_airport:
            origin_airport = random.choice(airports)
        if not dest_airport:
            dest_airport = random.choice([a for a in airports if a["iata"] != origin_airport["iata"]])
        
        market_data = []
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Generate data for each day
        for day in range(days):
            date = today - timedelta(days=day)
            
            # Generate random metrics with some seasonality (higher on weekends)
            is_weekend = date.weekday() >= 5
            base_demand = random.uniform(50, 200)
            weekend_boost = 1.5 if is_weekend else 1.0
            
            # Generate metrics with some randomness and trends
            search_volume = int(base_demand * weekend_boost * random.uniform(0.8, 1.2))
            booking_count = int(search_volume * random.uniform(0.1, 0.4))  # 10-40% conversion
            avg_price = round(random.uniform(150, 500) * (1.2 if is_weekend else 1.0), 2)
            
            # Add some day-of-week and time-of-day patterns
            day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
            time_of_day = date.hour if hasattr(date, 'hour') else 12
            
            # More searches in the morning and evening
            time_factor = 1.0
            if 7 <= time_of_day < 10 or 17 <= time_of_day < 21:
                time_factor = 1.3
            
            # Adjust metrics based on day and time
            search_volume = int(search_volume * time_factor)
            
            data_point = {
                "date": date.isoformat(),
                "origin": origin_airport["iata"],
                "destination": dest_airport["iata"],
                "search_volume": search_volume,
                "booking_count": booking_count,
                "conversion_rate": round(booking_count / search_volume * 100, 2) if search_volume > 0 else 0,
                "average_price": avg_price,
                "min_price": round(avg_price * random.uniform(0.7, 0.95), 2),
                "max_price": round(avg_price * random.uniform(1.05, 1.3), 2),
                "load_factor": round(random.uniform(60, 95), 1),  # 60-95% load factor
                "data_source": "mock"
            }
            
            market_data.append(data_point)
        
        # Sort by date (oldest first)
        market_data.sort(key=lambda x: x["date"])
        
        return market_data
    
    @staticmethod
    def get_airport_analytics(airport_code: str, days: int = 30) -> Dict[str, Any]:
        """Generate mock analytics data for a specific airport.
        
        Args:
            airport_code: IATA code of the airport
            days: Number of days of historical data to generate
            
        Returns:
            Dictionary with airport analytics data.
        """
        # Find the airport
        airport = next((a for a in AUSTRALIAN_AIRPORTS if a["iata"] == airport_code), None)
        if not airport:
            raise ValueError(f"Airport with code {airport_code} not found")
        
        # Get top destinations (random sample of other airports)
        other_airports = [a for a in AUSTRALIAN_AIRPORTS if a["iata"] != airport_code]
        top_destinations = random.sample(other_airports, min(5, len(other_airports)))
        
        # Generate time series data for the past N days
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        
        # Generate random time series data
        def generate_time_series(base_value: float, volatility: float = 0.2) -> List[float]:
            series = [base_value * random.uniform(0.9, 1.1)]
            for _ in range(1, days):
                prev = series[-1]
                change = prev * random.uniform(-volatility, volatility)
                series.append(round(prev + change, 2))
            return series
        
        # Generate analytics data
        analytics = {
            "airport": airport,
            "time_period": f"Last {days} days",
            "total_flights": random.randint(1000, 5000),
            "total_passengers": random.randint(100000, 500000),
            "average_load_factor": round(random.uniform(70, 90), 1),
            "on_time_performance": round(random.uniform(75, 95), 1),
            "top_destinations": [
                {
                    "airport": dest,
                    "flight_count": random.randint(50, 200),
                    "average_price": round(random.uniform(150, 500), 2),
                    "load_factor": round(random.uniform(60, 95), 1)
                }
                for dest in top_destinations
            ],
            "time_series": {
                "dates": dates,
                "flights": generate_time_series(100, 0.15),
                "passengers": generate_time_series(1000, 0.2),
                "load_factors": generate_time_series(80, 0.1),
                "average_fares": generate_time_series(250, 0.15)
            },
            "data_source": "mock"
        }
        
        return analytics
