"""
Flights API endpoints.
"""
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from pydantic.fields import Field

from app.services.data_service import DataService, DataServiceError
from app.api.deps import get_data_service

router = APIRouter()

# Request/Response Models
class FlightSegment(BaseModel):
    """Flight segment model."""
    departure_airport: str = Field(..., description="IATA code of departure airport")
    arrival_airport: str = Field(..., description="IATA code of arrival airport")
    departure_time: datetime = Field(..., description="Scheduled departure time")
    arrival_time: datetime = Field(..., description="Scheduled arrival time")
    flight_number: str = Field(..., description="Flight number")
    airline_code: str = Field(..., description="Airline IATA code")
    aircraft_type: Optional[str] = Field(None, description="Aircraft type code")
    duration_minutes: int = Field(..., description="Flight duration in minutes")
    cabin_class: str = Field(..., description="Cabin class (ECONOMY, BUSINESS, etc.)")

class FlightOffer(BaseModel):
    """Flight offer model."""
    id: str = Field(..., description="Unique identifier for the offer")
    price: float = Field(..., description="Total price in the specified currency")
    currency: str = Field(..., description="Currency code (e.g., AUD, USD)")
    departure_date: date = Field(..., description="Outbound departure date")
    return_date: Optional[date] = Field(None, description="Return date for round-trip")
    origin: str = Field(..., description="Origin airport IATA code")
    destination: str = Field(..., description="Destination airport IATA code")
    airline: str = Field(..., description="Airline IATA code")
    flight_number: str = Field(..., description="Flight number")
    available_seats: int = Field(..., description="Number of available seats")
    segments: List[FlightSegment] = Field(..., description="Flight segments")
    booking_url: Optional[HttpUrl] = Field(None, description="URL to book this flight")
    is_direct: bool = Field(..., description="Whether the flight is direct")
    is_mock: bool = Field(False, description="Whether this is mock data")

class FlightSearchRequest(BaseModel):
    """Flight search request model."""
    origin: str = Field(..., description="Origin airport IATA code")
    destination: str = Field(..., description="Destination airport IATA code")
    departure_date: date = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: Optional[date] = Field(None, description="Return date for round-trip (YYYY-MM-DD)")
    adults: int = Field(1, ge=1, le=9, description="Number of adult passengers")
    children: int = Field(0, ge=0, le=8, description="Number of child passengers")
    infants: int = Field(0, ge=0, le=8, description="Number of infant passengers")
    travel_class: str = Field("ECONOMY", description="Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)")
    non_stop: bool = Field(False, description="Only show non-stop flights")
    max_price: Optional[int] = Field(None, description="Maximum price per traveler")
    currency: str = Field("AUD", description="Currency code (default: AUD)")
    include_airlines: Optional[List[str]] = Field(None, description="Filter by airline IATA codes")
    exclude_airlines: Optional[List[str]] = Field(None, description="Exclude airline IATA codes")
    use_real_data: bool = Field(True, description="Whether to use real data (fallback to mock if unavailable)")

class FlightSearchResponse(BaseModel):
    """Flight search response model."""
    success: bool = Field(..., description="Whether the request was successful")
    data: List[FlightOffer] = Field(..., description="List of flight offers")
    count: int = Field(..., description="Total number of offers")
    metadata: dict = Field(..., description="Response metadata")

# API Endpoints
@router.get("/search", response_model=FlightSearchResponse)
async def search_flights(
    origin: str = Query(..., description="Origin airport IATA code"),
    destination: str = Query(..., description="Destination airport IATA code"),
    departure_date: date = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[date] = Query(None, description="Return date for round-trip (YYYY-MM-DD)"),
    adults: int = Query(1, ge=1, le=9, description="Number of adult passengers"),
    children: int = Query(0, ge=0, le=8, description="Number of child passengers"),
    infants: int = Query(0, ge=0, le=8, description="Number of infant passengers"),
    travel_class: str = Query("ECONOMY", description="Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)"),
    non_stop: bool = Query(False, description="Only show non-stop flights"),
    max_price: Optional[int] = Query(None, description="Maximum price per traveler"),
    currency: str = Query("AUD", description="Currency code (default: AUD)"),
    include_airlines: Optional[List[str]] = Query(None, description="Filter by airline IATA codes"),
    exclude_airlines: Optional[List[str]] = Query(None, description="Exclude airline IATA codes"),
    use_real_data: bool = Query(True, description="Whether to use real data (fallback to mock if unavailable)"),
    data_service: DataService = Depends(get_data_service)
):
    """
    Search for flight offers between two airports.
    
    This endpoint searches for available flights based on the provided criteria.
    It can return both real data from flight providers or mock data for testing.
    """
    try:
        # Convert date objects to strings in YYYY-MM-DD format
        departure_date_str = departure_date.strftime("%Y-%m-%d")
        return_date_str = return_date.strftime("%Y-%m-%d") if return_date else None
        
        # Call the data service to get flight offers
        result = await data_service.get_flight_offers(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure_date_str,
            return_date=return_date_str,
            adults=adults,
            children=children,
            infants=infants,
            travel_class=travel_class.upper(),
            non_stop=non_stop,
            max_price=max_price,
            currency=currency.upper(),
            include_airlines=[a.upper() for a in include_airlines] if include_airlines else None,
            exclude_airlines=[a.upper() for a in exclude_airlines] if exclude_airlines else None,
            use_real_data=use_real_data
        )
        
        # Extract the data and metadata from the result
        data = result.get("data", {})
        metadata = result.get("metadata", {})
        
        # Convert the data to our response model
        offers = []
        if isinstance(data, dict) and "flights" in data:
            # Mock data format
            for flight in data["flights"]:
                segment = FlightSegment(
                    departure_airport=flight["origin"]["iata"],
                    arrival_airport=flight["destination"]["iata"],
                    departure_time=datetime.fromisoformat(flight["departure_time"]),
                    arrival_time=datetime.fromisoformat(flight["arrival_time"]),
                    flight_number=flight["flight_number"],
                    airline_code=flight["airline"]["iata"],
                    aircraft_type=flight.get("aircraft_type"),
                    duration_minutes=flight["duration"],
                    cabin_class=flight.get("cabin_class", "ECONOMY")
                )
                
                offer = FlightOffer(
                    id=flight["id"],
                    price=flight["price"],
                    currency=flight["currency"],
                    departure_date=datetime.fromisoformat(flight["departure_time"]).date(),
                    origin=flight["origin"]["iata"],
                    destination=flight["destination"]["iata"],
                    airline=flight["airline"]["iata"],
                    flight_number=flight["flight_number"],
                    available_seats=flight["available_seats"],
                    segments=[segment],
                    is_direct=flight.get("is_direct", True),
                    is_mock=data.get("is_mock", False)
                )
                offers.append(offer)
        elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            # Amadeus API format
            for offer in data["data"]:
                # Parse Amadeus offer format
                segments = []
                for itinerary in offer.get("itineraries", []):
                    for segment in itinerary.get("segments", []):
                        segments.append(FlightSegment(
                            departure_airport=segment["departure"]["iataCode"],
                            arrival_airport=segment["arrival"]["iataCode"],
                            departure_time=datetime.fromisoformat(segment["departure"]["at"]),
                            arrival_time=datetime.fromisoformat(segment["arrival"]["at"]),
                            flight_number=f"{segment['carrierCode']}{segment['number']}",
                            airline_code=segment["carrierCode"],
                            aircraft_type=segment.get("aircraft", {}).get("code"),
                            duration_minutes=int(segment["duration"][2:-1]) if "duration" in segment else 0,
                            cabin_class=offer.get("travelerPricings", [{}])[0].get("fareDetailsBySegment", [{}])[0].get("cabin", "ECONOMY")
                        ))
                
                if segments:
                    price_info = offer.get("price", {})
                    offers.append(FlightOffer(
                        id=offer["id"],
                        price=float(price_info.get("total", 0)),
                        currency=price_info.get("currency", "AUD"),
                        departure_date=segments[0].departure_time.date(),
                        return_date=segments[-1].departure_time.date() if len(segments) > 1 else None,
                        origin=segments[0].departure_airport,
                        destination=segments[-1].arrival_airport,
                        airline=segments[0].airline_code,
                        flight_number=segments[0].flight_number,
                        available_seats=offer.get("numberOfBookableSeats", 1),
                        segments=segments,
                        is_direct=all(s.departure_airport == segments[0].departure_airport 
                                   and s.arrival_airport == segments[-1].arrival_airport 
                                   for s in segments),
                        is_mock=False
                    ))
        
        return {
            "success": True,
            "data": offers,
            "count": len(offers),
            "metadata": metadata
        }
        
    except DataServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching flight data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
