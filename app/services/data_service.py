"""
Data service for fetching and processing airline market data.

This module provides a unified interface for accessing flight and market data
from various sources, with automatic fallback to mock data when needed.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum, auto
from fastapi import HTTPException, status

from app.core.config import settings
from .amadeus_client import AmadeusClient, AmadeusClientError
from .rapidapi_client import RapidApiClient
from .aviationstack_client import AviationStackClient
from .mock_data_provider import MockDataProvider
from .config import get_config, AmadeusConfig, RapidApiConfig, AviationStackConfig

# Configure logging
logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Enumeration of available data sources."""
    AMADEUS = auto()
    RAPIDAPI = auto()
    AVIATIONSTACK = auto()
    MOCK = auto()

class DataServiceError(Exception):
    """Custom exception for data service errors."""
    def __init__(self, message: str, source: DataSource = None, status_code: int = None):
        self.message = message
        self.source = source
        self.status_code = status_code
        super().__init__(self.message)

class DataService:
    """Service for accessing and processing airline market data."""
    
    def __init__(self):
        """Initialize the data service with configured providers."""
        self.mock_provider = MockDataProvider()
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """Initialize API clients based on configuration."""
        # Initialize Amadeus client if configured
        if settings.AMADEUS_API_KEY and settings.AMADEUS_API_SECRET:
            amadeus_config = AmadeusConfig(
                api_key=settings.AMADEUS_API_KEY,
                api_secret=settings.AMADEUS_API_SECRET
            )
            self.clients[DataSource.AMADEUS] = AmadeusClient(amadeus_config)
        
        # Initialize RapidAPI client if configured
        if settings.RAPIDAPI_KEY:
            rapidapi_config = RapidApiConfig(api_key=settings.RAPIDAPI_KEY)
            self.clients[DataSource.RAPIDAPI] = RapidApiClient(rapidapi_config)
        
        # Initialize AviationStack client if configured
        if settings.AVIATIONSTACK_ACCESS_KEY:
            avstack_config = AviationStackConfig(access_key=settings.AVIATIONSTACK_ACCESS_KEY)
            self.clients[DataSource.AVIATIONSTACK] = AviationStackClient(avstack_config)
        
        # Always have mock data available as fallback
        self.clients[DataSource.MOCK] = self.mock_provider
        
        logger.info(f"Initialized data service with clients: {list(self.clients.keys())}")
    
    async def _with_fallback(
        self, 
        func: callable, 
        source: DataSource, 
        fallback_sources: List[Tuple[DataSource, str]] = None,
        **kwargs
    ) -> Any:
        """Execute a function with fallback to other sources on failure.
        
        Args:
            func: Function to execute (takes source as first argument)
            source: Primary data source to try first
            fallback_sources: List of (source, description) tuples to try if primary fails
            **kwargs: Additional arguments to pass to the function
            
        Returns:
            Result from the first successful source
            
        Raises:
            DataServiceError: If all sources fail and no fallback is available
        """
        # Try primary source first
        if source in self.clients:
            try:
                logger.info(f"Trying {source.name}...")
                result = await func(source, **kwargs)
                if result is not None:
                    return {"data": result, "source": source.name}
            except Exception as e:
                logger.warning(f"{source.name} failed: {str(e)}")
        else:
            logger.warning(f"{source.name} client not configured")
        
        # Try fallback sources
        if fallback_sources:
            for fallback_source, description in fallback_sources:
                if fallback_source in self.clients and fallback_source != source:
                    try:
                        logger.info(f"Falling back to {fallback_source.name} ({description})...")
                        result = await func(fallback_source, **kwargs)
                        if result is not None:
                            return {"data": result, "source": fallback_source.name, "fallback": True}
                    except Exception as e:
                        logger.warning(f"{fallback_source.name} fallback failed: {str(e)}")
        
        # If we get here, all sources failed
        error_msg = f"All data sources failed for {func.__name__}"
        logger.error(error_msg)
        raise DataServiceError(error_msg, source=source, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    async def get_airports(
        self, 
        search: Optional[str] = None,
        country: Optional[str] = None,
        iata_code: Optional[str] = None,
        use_real_data: bool = True
    ) -> Dict[str, Any]:
        """Get a list of airports with optional filtering.
        
        Args:
            search: Optional search term for airport name, city, or country
            country: Filter by country name
            iata_code: Filter by IATA code
            use_real_data: Whether to try real data sources first
            
        Returns:
            Dictionary containing list of airports and metadata
            
        Raises:
            DataServiceError: If no data sources are available
        """
        async def fetch_airports(source: DataSource, **kwargs) -> List[Dict[str, Any]]:
            if source == DataSource.AMADEUS:
                # Amadeus doesn't have a direct airports endpoint, use mock
                return None
            elif source == DataSource.RAPIDAPI:
                params = {}
                if search:
                    params["search"] = search
                if country:
                    params["country_name"] = country
                if iata_code:
                    params["iata_code"] = iata_code
                response = await self.clients[source].get_airports(**params)
                return response.get("data", [])
            elif source == DataSource.AVIATIONSTACK:
                params = {}
                if search:
                    params["search"] = search
                if country:
                    params["country_name"] = country
                if iata_code:
                    params["iata_code"] = iata_code
                response = await self.clients[source].get_airports(**params)
                return response.get("data", [])
            elif source == DataSource.MOCK:
                airports = self.mock_provider.get_airports()
                # Apply filters
                if search:
                    search_lower = search.lower()
                    airports = [
                        ap for ap in airports 
                        if (search_lower in ap["name"].lower() or 
                            search_lower in ap["city"].lower() or 
                            search_lower in ap["country"].lower() or
                            search_lower == ap["iata"].lower() or
                            (ap.get("icao") and search_lower == ap["icao"].lower()))
                    ]
                if country:
                    country_lower = country.lower()
                    airports = [ap for ap in airports if country_lower in ap["country"].lower()]
                if iata_code:
                    iata_code_upper = iata_code.upper()
                    airports = [ap for ap in airports if ap["iata"] == iata_code_upper]
                return airports
            return None
        
        # Define fallback sources
        fallback_sources = [
            (DataSource.RAPIDAPI, "RapidAPI"),
            (DataSource.AVIATIONSTACK, "AviationStack"),
            (DataSource.MOCK, "Mock Data")
        ]
        
        # Determine primary source
        primary_source = DataSource.AMADEUS if use_real_data and DataSource.AMADEUS in self.clients else DataSource.MOCK
        
        try:
            return await self._with_fallback(
                fetch_airports,
                source=primary_source,
                fallback_sources=fallback_sources if use_real_data else None,
                search=search,
                country=country,
                iata_code=iata_code
            )
        except DataServiceError as e:
            # If all else fails, return mock data
            return {
                "data": self.mock_provider.get_airports(),
                "source": "mock",
                "warning": str(e)
            }
    
    async def search_flight_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        travel_class: str = "ECONOMY",
        non_stop: bool = False,
        currency: str = "AUD",
        max_price: float = None,
        include_airlines: List[str] = None,
        exclude_airlines: List[str] = None,
        use_real_data: bool = True
    ) -> Dict[str, Any]:
        """
        Search for flight offers across all available data sources with fallback.
        
        Args:
            origin: Origin IATA code (e.g., 'SYD')
            destination: Destination IATA code (e.g., 'MEL')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (for round trips)
            adults: Number of adult passengers
            children: Number of child passengers
            infants: Number of infant passengers
            travel_class: Travel class (e.g., 'ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST')
            non_stop: Whether to return only non-stop flights
            currency: Currency code for pricing
            max_price: Maximum price filter
            include_airlines: List of airline IATA codes to include (None for all)
            exclude_airlines: List of airline IATA codes to exclude
            use_real_data: Whether to try real data providers first
            
        Returns:
            Dictionary containing flight offers and metadata
        """
        # Prepare common parameters
        common_params = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            "children": children,
            "infants": infants,
            "travel_class": travel_class,
            "non_stop": non_stop,
            "currency": currency
        }
        
        # Initialize result structure
        result = {
            "data": [],
            "meta": {
                "count": 0,
                "sources_tried": [],
                "sources_succeeded": []
            },
            "is_mock": False
        }
        
        # Define fetch function for _with_fallback
        async def fetch_flights(source: DataSource) -> Optional[Dict]:
            if source == DataSource.AMADEUS:
                amadeus_params = common_params.copy()
                return await self.clients[source].search_flights(**amadeus_params)
            elif source == DataSource.RAPIDAPI:
                rapidapi_params = common_params.copy()
                return await self.clients[source].search_flights(**rapidapi_params)
            elif source == DataSource.AVIATIONSTACK:
                # AviationStack doesn't support flight offers, use mock
                return None
            elif source == DataSource.MOCK:
                # Use mock data provider
                departure_dt = datetime.strptime(departure_date, "%Y-%m-%d")
                return_dt = datetime.strptime(return_date, "%Y-%m-%d") if return_date else None
                return self.mock_provider.get_flights(
                    origin=origin,
                    destination=destination,
                    date_from=departure_dt,
                    date_to=return_dt or (departure_dt + timedelta(days=1)),
                    limit=10  # Limit mock results for performance
                )
            return None
        
        # Define fallback sources
        fallback_sources = [
            (DataSource.RAPIDAPI, "RapidAPI"),
            (DataSource.MOCK, "Mock Data")
        ]
        
        # Determine primary source
        primary_source = DataSource.AMADEUS if use_real_data and DataSource.AMADEUS in self.clients else DataSource.MOCK
        
        try:
            result = await self._with_fallback(
                fetch_flights,
                source=primary_source,
                fallback_sources=fallback_sources if use_real_data else None
            )
            
            # Apply any post-processing
            if result and "data" in result and result["data"]:
                # Filter by max price if specified
                if max_price is not None:
                    result["data"] = [
                        offer for offer in result["data"] 
                        if float(offer.get("price", {}).get("total", float('inf'))) <= max_price
                    ]
                
                # Filter airlines if specified
                if include_airlines or exclude_airlines:
                    filtered_offers = []
                    for offer in result["data"]:
                        # Get all airline codes from the offer
                        airlines = set()
                        for segment in offer.get("itineraries", [{}])[0].get("segments", []):
                            if "carrierCode" in segment:
                                airlines.add(segment["carrierCode"])
                        
                        # Apply filters
                        include = True
                        if include_airlines and not any(airline in include_airlines for airline in airlines):
                            include = False
                        if exclude_airlines and any(airline in exclude_airlines for airline in airlines):
                            include = False
                            
                        if include:
                            filtered_offers.append(offer)
                    
                    result["data"] = filtered_offers
                    result["meta"]["count"] = len(filtered_offers)
            
            return result
            
        except DataServiceError as e:
            # If all else fails, return mock data with error info
            departure_dt = datetime.strptime(departure_date, "%Y-%m-%d")
            return_dt = datetime.strptime(return_date, "%Y-%m-%d") if return_date else None
            
            return {
                "data": self.mock_provider.get_flights(
                    origin=origin,
                    destination=destination,
                    date_from=departure_dt,
                    date_to=return_dt or (departure_dt + timedelta(days=1)),
                    limit=10
                ),
                "source": "mock",
                "warning": f"All data sources failed: {str(e)}",
                "is_mock": True
            },
            "metadata": {
                "source": "mock",
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "Using mock data - real data source unavailable"
            }
        }
    
    async def get_market_data(
        self,
        origin: str,
        destination: str,
        days: int = 30,
        use_real_data: bool = True
    ) -> Dict[str, Any]:
        """Get market data for a route.
        
        Args:
            origin: Origin airport IATA code
            destination: Destination airport IATA code
            days: Number of days of historical data to return
            use_real_data: Whether to attempt to use real data (fallback to mock if unavailable)
            
        Returns:
            Dictionary containing market data
            
        Raises:
            HTTPException: If the request fails and no fallback is available
        """
        # For now, we only have mock data for market data
        logger.info(f"Getting market data for {origin}-{destination} for the last {days} days")
        
        market_data = self.mock_provider.get_market_data(
            origin=origin,
            destination=destination,
            days=days
        )
        
        return {
            "data": market_data,
            "metadata": {
                "source": "mock",
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "Using mock data - real market data not yet implemented"
            }
        }
    
    async def get_airport_analytics(
        self,
        airport_code: str,
        days: int = 30,
        use_real_data: bool = True
    ) -> Dict[str, Any]:
        """Get analytics data for a specific airport.
        
        Args:
            airport_code: IATA code of the airport
            days: Number of days of historical data to return
            use_real_data: Whether to attempt to use real data (fallback to mock if unavailable)
            
        Returns:
            Dictionary containing airport analytics data
            
        Raises:
            HTTPException: If the request fails and no fallback is available
        """
        # Try to use real data if requested and available
        if use_real_data and self.amadeus_client:
            try:
                logger.info(f"Fetching real analytics for airport {airport_code}")
                result = await self.amadeus_client.get_flight_most_traveled_destinations(
                    origin_city_code=airport_code,
                    period=datetime.utcnow().strftime("%Y-%m"),
                    max_destinations=5,
                    use_mock_fallback=True
                )
                
                # If we got real data, return it
                if result and not result.get('is_mock', False):
                    return {
                        "data": result,
                        "metadata": {
                            "source": "amadeus",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                
            except AmadeusClientError as e:
                logger.warning(f"Failed to fetch real airport analytics: {str(e)}")
                if not use_real_data:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Failed to fetch airport analytics from provider"
                    )
        
        # Fall back to mock data
        logger.info(f"Using mock data for airport analytics for {airport_code}")
        analytics = self.mock_provider.get_airport_analytics(
            airport_code=airport_code,
            days=days
        )
        
        return {
            "data": analytics,
            "metadata": {
                "source": "mock",
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "Using mock data - real analytics not available"
            }
        }
