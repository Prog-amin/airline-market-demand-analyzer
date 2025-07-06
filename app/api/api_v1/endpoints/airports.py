"""
Airports API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.data_service import DataService, DataServiceError
from app.api.deps import get_data_service

router = APIRouter()

# Request/Response Models
class Airport(BaseModel):
    """Airport model."""
    iata_code: str = Field(..., description="IATA airport code (3 letters)")
    icao_code: Optional[str] = Field(None, description="ICAO airport code (4 letters)")
    name: str = Field(..., description="Airport name")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country name")
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    timezone: Optional[str] = Field(None, description="IANA timezone name")
    timezone_offset: Optional[int] = Field(None, description="Timezone offset from UTC in hours")

class AirportResponse(BaseModel):
    """Airport response model."""
    success: bool = Field(..., description="Whether the request was successful")
    data: List[Airport] = Field(..., description="List of airports")
    count: int = Field(..., description="Total number of airports")
    metadata: dict = Field(..., description="Response metadata")

class AirportAnalytics(BaseModel):
    """Airport analytics model."""
    airport: Airport = Field(..., description="Airport information")
    time_period: str = Field(..., description="Time period for the analytics")
    total_flights: int = Field(..., description="Total number of flights")
    total_passengers: int = Field(..., description="Total number of passengers")
    average_load_factor: float = Field(..., description="Average load factor (percentage)")
    on_time_performance: float = Field(..., description="On-time performance (percentage)")
    top_destinations: List[dict] = Field(..., description="Top destinations from this airport")
    time_series: dict = Field(..., description="Time series data for various metrics")

class AirportAnalyticsResponse(BaseModel):
    """Airport analytics response model."""
    success: bool = Field(..., description="Whether the request was successful")
    data: AirportAnalytics = Field(..., description="Airport analytics data")
    metadata: dict = Field(..., description="Response metadata")

# API Endpoints
@router.get("", response_model=AirportResponse)
async def list_airports(
    query: Optional[str] = Query(None, description="Search query for airport name, city, or IATA code"),
    country: Optional[str] = Query(None, description="Filter by country name"),
    data_service: DataService = Depends(get_data_service)
):
    """
    Get a list of airports.
    
    This endpoint returns a list of airports, optionally filtered by search query or country.
    """
    try:
        # Get all airports from the data service
        airports_data = await data_service.get_airports()
        
        # Apply filters if provided
        filtered_airports = []
        for airport in airports_data:
            # Apply search query filter
            if query and query.lower() not in (
                airport["iata"].lower(),
                airport.get("icao", "").lower(),
                airport["name"].lower(),
                airport["city"].lower()
            ):
                continue
                
            # Apply country filter
            if country and country.lower() not in airport["country"].lower():
                continue
                
            # Convert to our model
            filtered_airports.append(Airport(
                iata_code=airport["iata"],
                icao_code=airport.get("icao"),
                name=airport["name"],
                city=airport["city"],
                country=airport["country"],
                latitude=airport["lat"],
                longitude=airport["lon"],
                timezone=airport.get("timezone"),
                timezone_offset=airport.get("timezone_offset")
            ))
        
        return {
            "success": True,
            "data": filtered_airports,
            "count": len(filtered_airports),
            "metadata": {
                "source": "mock",  # Currently only mock data is available
                "timestamp": "2023-01-01T00:00:00Z",
                "warning": "Using mock data - real airport data not yet implemented"
            }
        }
        
    except DataServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching airport data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/{iata_code}", response_model=AirportResponse)
async def get_airport(
    iata_code: str,
    data_service: DataService = Depends(get_data_service)
):
    """
    Get details for a specific airport by IATA code.
    
    Args:
        iata_code: IATA airport code (3 letters)
    """
    try:
        # Get all airports from the data service
        airports_data = await data_service.get_airports()
        
        # Find the airport with the matching IATA code
        for airport in airports_data:
            if airport["iata"].upper() == iata_code.upper():
                airport_model = Airport(
                    iata_code=airport["iata"],
                    icao_code=airport.get("icao"),
                    name=airport["name"],
                    city=airport["city"],
                    country=airport["country"],
                    latitude=airport["lat"],
                    longitude=airport["lon"],
                    timezone=airport.get("timezone"),
                    timezone_offset=airport.get("timezone_offset")
                )
                
                return {
                    "success": True,
                    "data": [airport_model],
                    "count": 1,
                    "metadata": {
                        "source": "mock",
                        "timestamp": "2023-01-01T00:00:00Z"
                    }
                }
        
        # If we get here, the airport wasn't found
        raise HTTPException(
            status_code=404,
            detail=f"Airport with IATA code '{iata_code}' not found"
        )
        
    except HTTPException:
        raise
    except DataServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching airport data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/{iata_code}/analytics", response_model=AirportAnalyticsResponse)
async def get_airport_analytics(
    iata_code: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of historical data to include"),
    use_real_data: bool = Query(True, description="Whether to use real data (fallback to mock if unavailable)"),
    data_service: DataService = Depends(get_data_service)
):
    """
    Get analytics data for a specific airport.
    
    This endpoint returns various analytics and statistics for the specified airport,
    including traffic data, popular routes, and historical trends.
    
    Args:
        iata_code: IATA airport code (3 letters)
        days: Number of days of historical data to include (1-365)
        use_real_data: Whether to use real data (fallback to mock if unavailable)
    """
    try:
        # Get analytics data from the data service
        result = await data_service.get_airport_analytics(
            airport_code=iata_code.upper(),
            days=days,
            use_real_data=use_real_data
        )
        
        # Extract the data and metadata
        analytics_data = result.get("data", {})
        metadata = result.get("metadata", {})
        
        # Get the airport details
        airport_data = analytics_data.get("airport", {})
        airport = Airport(
            iata_code=airport_data.get("iata"),
            icao_code=airport_data.get("icao"),
            name=airport_data.get("name"),
            city=airport_data.get("city"),
            country=airport_data.get("country"),
            latitude=airport_data.get("lat"),
            longitude=airport_data.get("lon"),
            timezone=airport_data.get("timezone"),
            timezone_offset=airport_data.get("timezone_offset")
        )
        
        # Create the analytics model
        analytics = AirportAnalytics(
            airport=airport,
            time_period=analytics_data.get("time_period", f"Last {days} days"),
            total_flights=analytics_data.get("total_flights", 0),
            total_passengers=analytics_data.get("total_passengers", 0),
            average_load_factor=analytics_data.get("average_load_factor", 0.0),
            on_time_performance=analytics_data.get("on_time_performance", 0.0),
            top_destinations=analytics_data.get("top_destinations", []),
            time_series=analytics_data.get("time_series", {})
        )
        
        return {
            "success": True,
            "data": analytics,
            "metadata": metadata
        }
        
    except DataServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching airport analytics: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
