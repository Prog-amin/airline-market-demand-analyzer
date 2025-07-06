"""
Market data API endpoints.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator

from app.services.data_service import DataService, DataServiceError
from app.api.deps import get_data_service

router = APIRouter()

# Request/Response Models
class MarketDataPoint(BaseModel):
    """A single data point in a market data series."""
    date: date = Field(..., description="The date of the data point")
    value: float = Field(..., description="The value of the data point")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the data point")

class MarketDataSeries(BaseModel):
    """A named series of market data points."""
    name: str = Field(..., description="Name of the data series")
    description: Optional[str] = Field(None, description="Description of what this series represents")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., 'AUD', 'seats', 'flights')")
    data: List[MarketDataPoint] = Field(..., description="The data points in this series")

class MarketDataResponse(BaseModel):
    """Response model for market data endpoints."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Dict[str, MarketDataSeries] = Field(..., description="Market data series keyed by name")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")

class RouteDemand(BaseModel):
    """Demand data for a specific route."""
    origin: str = Field(..., description="Origin airport IATA code")
    destination: str = Field(..., description="Destination airport IATA code")
    departure_date: date = Field(..., description="Departure date")
    average_price: float = Field(..., description="Average price in the specified currency")
    median_price: float = Field(..., description="Median price in the specified currency")
    min_price: float = Field(..., description="Minimum price in the specified currency")
    max_price: float = Field(..., description="Maximum price in the specified currency")
    available_seats: int = Field(..., description="Total number of available seats")
    total_flights: int = Field(..., description="Total number of flights")
    load_factor: float = Field(..., description="Average load factor (0-1)")
    currency: str = Field(..., description="Currency code (e.g., 'AUD')")
    is_prediction: bool = Field(False, description="Whether this is a prediction or actual data")
    confidence: Optional[float] = Field(None, description="Confidence score for predictions (0-1)", ge=0, le=1)

class RouteDemandResponse(BaseModel):
    """Response model for route demand data."""
    success: bool = Field(..., description="Whether the request was successful")
    data: List[RouteDemand] = Field(..., description="List of route demand data points")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")

class PriceTrendsRequest(BaseModel):
    """Request model for price trends."""
    origin: str = Field(..., description="Origin airport IATA code")
    destination: str = Field(..., description="Destination airport IATA code")
    departure_date_range: tuple[date, date] = Field(
        ...,
        description="Date range for the query (start_date, end_date)"
    )
    booking_window_days: int = Field(
        90,
        ge=1,
        le=365,
        description="Number of days before departure to include in the analysis"
    )
    currency: str = Field("AUD", description="Currency for price data")
    use_real_data: bool = Field(True, description="Whether to use real data (fallback to mock if unavailable)")

    @validator('departure_date_range')
    def validate_date_range(cls, v):
        start_date, end_date = v
        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")
        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 1 year")
        return v

# API Endpoints
@router.get("/prices/trends", response_model=MarketDataResponse)
async def get_price_trends(
    origin: str = Query(..., description="Origin airport IATA code"),
    destination: str = Query(..., description="Destination airport IATA code"),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    booking_window_days: int = Query(90, ge=1, le=365, description="Booking window in days"),
    currency: str = Query("AUD", description="Currency code (e.g., 'AUD')"),
    use_real_data: bool = Query(True, description="Whether to use real data (fallback to mock if unavailable)"),
    data_service: DataService = Depends(get_data_service)
):
    """
    Get price trends for a specific route over time.
    
    This endpoint returns historical price data for flights between the specified
    origin and destination airports, aggregated by day.
    """
    try:
        # Get market data from the data service
        result = await data_service.get_market_data(
            origin=origin.upper(),
            destination=destination.upper(),
            days=(end_date - start_date).days,
            use_real_data=use_real_data
        )
        
        # Extract the data and metadata
        market_data = result.get("data", {})
        metadata = result.get("metadata", {})
        
        # Transform the data into the expected format
        price_series = []
        load_factor_series = []
        
        for date_str, data_point in market_data.items():
            try:
                point_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if start_date <= point_date <= end_date:
                    price_series.append(MarketDataPoint(
                        date=point_date,
                        value=data_point.get("average_price", 0),
                        metadata={
                            "min_price": data_point.get("min_price"),
                            "max_price": data_point.get("max_price"),
                            "booking_count": data_point.get("booking_count")
                        }
                    ))
                    
                    load_factor_series.append(MarketDataPoint(
                        date=point_date,
                        value=data_point.get("load_factor", 0) * 100,  # Convert to percentage
                        metadata={
                            "available_seats": data_point.get("available_seats"),
                            "booked_seats": data_point.get("booked_seats")
                        }
                    ))
            except (ValueError, TypeError):
                continue
        
        # Create the response
        response_data = {
            "prices": MarketDataSeries(
                name="Average Prices",
                description=f"Average ticket prices for {origin.upper()}-{destination.upper()}",
                unit=currency,
                data=sorted(price_series, key=lambda x: x.date)
            ),
            "load_factors": MarketDataSeries(
                name="Load Factors",
                description=f"Flight load factors for {origin.upper()}-{destination.upper()}",
                unit="%",
                data=sorted(load_factor_series, key=lambda x: x.date)
            )
        }
        
        return {
            "success": True,
            "data": response_data,
            "metadata": metadata
        }
        
    except DataServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching market data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/demand/route", response_model=RouteDemandResponse)
async def get_route_demand(
    origin: str = Query(..., description="Origin airport IATA code"),
    destination: str = Query(..., description="Destination airport IATA code"),
    departure_date: date = Query(..., description="Departure date (YYYY-MM-DD)"),
    days: int = Query(7, ge=1, le=30, description="Number of days to include in the analysis"),
    currency: str = Query("AUD", description="Currency code (e.g., 'AUD')"),
    use_real_data: bool = Query(True, description="Whether to use real data (fallback to mock if unavailable)"),
    data_service: DataService = Depends(get_data_service)
):
    """
    Get demand data for a specific route.
    
    This endpoint returns detailed demand information for flights between the specified
    origin and destination airports, including price statistics and seat availability.
    """
    try:
        # Calculate date range
        end_date = departure_date
        start_date = end_date - timedelta(days=days-1)
        
        # Get market data from the data service
        result = await data_service.get_market_data(
            origin=origin.upper(),
            destination=destination.upper(),
            days=days,
            use_real_data=use_real_data
        )
        
        # Extract the data and metadata
        market_data = result.get("data", {})
        metadata = result.get("metadata", {})
        
        # Transform the data into the expected format
        route_demands = []
        
        for date_str, data_point in market_data.items():
            try:
                point_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if start_date <= point_date <= end_date:
                    route_demands.append(RouteDemand(
                        origin=origin.upper(),
                        destination=destination.upper(),
                        departure_date=point_date,
                        average_price=data_point.get("average_price", 0),
                        median_price=data_point.get("median_price", 0),
                        min_price=data_point.get("min_price", 0),
                        max_price=data_point.get("max_price", 0),
                        available_seats=data_point.get("available_seats", 0),
                        total_flights=data_point.get("total_flights", 0),
                        load_factor=data_point.get("load_factor", 0),
                        currency=currency,
                        is_prediction=data_point.get("is_prediction", False),
                        confidence=data_point.get("confidence")
                    ))
            except (ValueError, TypeError):
                continue
        
        # Sort by departure date
        route_demands.sort(key=lambda x: x.departure_date)
        
        return {
            "success": True,
            "data": route_demands,
            "metadata": metadata
        }
        
    except DataServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching route demand data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@router.get("/insights", response_model=Dict[str, Any])
async def get_market_insights(
    origin: Optional[str] = Query(None, description="Filter by origin airport IATA code"),
    destination: Optional[str] = Query(None, description="Filter by destination airport IATA code"),
    days: int = Query(30, ge=1, le=180, description="Number of days to analyze"),
    use_real_data: bool = Query(True, description="Whether to use real data (fallback to mock if unavailable)"),
    data_service: DataService = Depends(get_data_service)
):
    """
    Get market insights and analytics.
    
    This endpoint provides high-level insights and analytics about the airline market,
    including trends, popular routes, and price movements.
    """
    try:
        # For now, we'll just return some mock insights
        # In a real implementation, this would analyze the market data
        
        insights = {
            "top_routes": [
                {"origin": "SYD", "destination": "MEL", "flights": 42, "average_price": 189.99},
                {"origin": "MEL", "destination": "SYD", "flights": 39, "average_price": 175.50},
                {"origin": "SYD", "destination": "BNE", "flights": 35, "average_price": 159.95},
                {"origin": "BNE", "destination": "MEL", "flights": 28, "average_price": 169.99},
                {"origin": "SYD", "destination": "PER", "flights": 25, "average_price": 289.50}
            ],
            "price_trends": {
                "up": ["SYD-MEL", "MEL-BNE"],
                "down": ["BNE-SYD", "MEL-PER"],
                "stable": ["SYD-PER", "MEL-ADL"]
            },
            "busiest_days": ["Friday", "Sunday", "Monday"],
            "cheapest_days": ["Tuesday", "Wednesday", "Saturday"],
            "average_load_factor": 0.78,
            "total_flights_analyzed": 1245,
            "period": f"Last {days} days",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Apply filters if provided
        if origin:
            insights["top_routes"] = [r for r in insights["top_routes"] if r["origin"] == origin.upper()]
        if destination:
            insights["top_routes"] = [r for r in insights["top_routes"] if r["destination"] == destination.upper()]
        
        return {
            "success": True,
            "data": insights,
            "metadata": {
                "source": "mock",
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "Using mock data - real insights not yet implemented"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
