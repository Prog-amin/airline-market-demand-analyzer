from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta
import logging

from app.db.base import get_db
from app.models.user import User
from app.schemas.flight import (
    FlightSearchQuery, FlightOffer, AirportInfo, 
    AirlineInfo, PriceHistoryResponse, SearchInsights, TravelClass
)
from app.services.flight import FlightService
from app.api.deps import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/search", response_model=dict)
async def search_flights(
    *,
    db: AsyncSession = Depends(get_db),
    search_query: FlightSearchQuery,
    current_user: Optional[User] = Depends(get_current_active_user),
) -> Any:
    """
    Search for flights based on the provided criteria.
    
    This endpoint searches for available flights between the specified origin and destination
    on the given dates. It supports one-way and round-trip searches with various filters.
    """
    try:
        flight_service = FlightService(db)
        results = await flight_service.search_flights(
            query=search_query,
            user=current_user
        )
        return results
    except Exception as e:
        logger.error(f"Error searching flights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching for flights"
        )

@router.get("/airports/{iata_code}", response_model=AirportInfo)
async def get_airport_info(
    *,
    db: AsyncSession = Depends(get_db),
    iata_code: str = Query(..., min_length=3, max_length=3, regex=r'^[A-Z]{3}$'),
) -> Any:
    """
    Get detailed information about an airport by its IATA code.
    
    This endpoint provides information such as airport name, location, terminals,
    facilities, and transportation options.
    """
    try:
        flight_service = FlightService(db)
        airport_info = await flight_service.get_airport_info(iata_code.upper())
        if not airport_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airport with IATA code {iata_code} not found"
            )
        return airport_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting airport info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving airport information"
        )

@router.get("/airlines/{iata_code}", response_model=AirlineInfo)
async def get_airline_info(
    *,
    db: AsyncSession = Depends(get_db),
    iata_code: str = Query(..., min_length=2, max_length=3, regex=r'^[A-Z0-9]{2,3}$'),
) -> Any:
    """
    Get information about an airline by its IATA code.
    
    This endpoint provides details about an airline, including its name, logo,
    and contact information.
    """
    try:
        # In a real implementation, this would fetch from a database or external API
        # For now, we'll return mock data
        airlines = {
            "QF": {"code": "QF", "name": "Qantas", "logo_url": "https://example.com/logos/qantas.png"},
            "VA": {"code": "VA", "name": "Virgin Australia", "logo_url": "https://example.com/logos/virgin.png"},
            "JQ": {"code": "JQ", "name": "Jetstar", "logo_url": "https://example.com/logos/jetstar.png"},
            "Rex": {"code": "Rex", "name": "Rex Airlines", "logo_url": "https://example.com/logos/rex.png"},
            "ZL": {"code": "ZL", "name": "Regional Express", "logo_url": "https://example.com/logos/rexpress.png"},
        }
        
        airline = airlines.get(iata_code.upper())
        if not airline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airline with IATA code {iata_code} not found"
            )
            
        return AirlineInfo(
            iata_code=airline["code"],
            name=airline["name"],
            logo_url=airline.get("logo_url"),
            website=f"https://www.{airline['name'].lower().replace(' ', '')}.com"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting airline info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving airline information"
        )

@router.get("/price-history", response_model=PriceHistoryResponse)
async def get_price_history(
    *,
    db: AsyncSession = Depends(get_db),
    origin: str = Query(..., min_length=3, max_length=3, regex=r'^[A-Z]{3}$'),
    destination: str = Query(..., min_length=3, max_length=3, regex=r'^[A-Z]{3}$'),
    departure_date: date,
    return_date: Optional[date] = None,
    travel_class: TravelClass = TravelClass.ECONOMY,
    days_back: int = Query(30, ge=1, le=365),
) -> Any:
    """
    Get historical price data for a specific route.
    
    This endpoint provides price history for flights between the specified origin
    and destination, helping users identify price trends and the best time to book.
    """
    try:
        flight_service = FlightService(db)
        return await flight_service.get_price_history(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure_date,
            return_date=return_date,
            days_back=days_back,
            travel_class=travel_class
        )
    except Exception as e:
        logger.error(f"Error getting price history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving price history"
        )

@router.get("/insights", response_model=SearchInsights)
async def get_search_insights(
    *,
    db: AsyncSession = Depends(get_db),
    origin: str = Query(..., min_length=3, max_length=3, regex=r'^[A-Z]{3}$'),
    destination: str = Query(..., min_length=3, max_length=3, regex=r'^[A-Z]{3}$'),
    days: int = Query(30, ge=7, le=365),
) -> Any:
    """
    Get search insights and analytics for a specific route.
    
    This endpoint provides data on search volume, average prices, and other
    insights to help users make informed booking decisions.
    """
    try:
        flight_service = FlightService(db)
        return await flight_service.get_search_insights(
            origin=origin.upper(),
            destination=destination.upper(),
            days=days
        )
    except Exception as e:
        logger.error(f"Error getting search insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving search insights"
        )

@router.get("/popular-routes")
async def get_popular_routes(
    *,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
) -> Any:
    """
    Get the most popular flight routes.
    
    This endpoint returns the most frequently searched routes, which can be useful
    for discovering popular travel destinations.
    """
    try:
        # In a real implementation, this would query the database for popular routes
        # For now, we'll return some mock data
        popular_routes = [
            {"origin": "SYD", "destination": "MEL", "searches": 12500},
            {"origin": "MEL", "destination": "SYD", "searches": 11800},
            {"origin": "SYD", "destination": "BNE", "searches": 9800},
            {"origin": "BNE", "destination": "SYD", "searches": 9500},
            {"origin": "MEL", "destination": "BNE", "searches": 8700},
            {"origin": "BNE", "destination": "MEL", "searches": 8400},
            {"origin": "SYD", "destination": "PER", "searches": 7600},
            {"origin": "PER", "destination": "SYD", "searches": 7200},
            {"origin": "MEL", "destination": "PER", "searches": 6800},
            {"origin": "PER", "destination": "MEL", "searches": 6500},
        ]
        
        return {"routes": popular_routes[:limit]}
    except Exception as e:
        logger.error(f"Error getting popular routes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving popular routes"
        )
