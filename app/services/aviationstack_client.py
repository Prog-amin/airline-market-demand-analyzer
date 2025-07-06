"""
AviationStack API client for fetching flight and airport data.

This module provides a client for interacting with the AviationStack API,
which provides real-time flight tracking, airport, and airline data.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union

from pydantic import BaseModel, Field, HttpUrl, validator

from .base_client import BaseApiClient, ApiClientError
from .config import AviationStackConfig
from .mock_data_provider import MockDataProvider

# Configure logging
logger = logging.getLogger(__name__)

# Models for request/response validation
class FlightSearchParams(BaseModel):
    """Parameters for flight search."""
    flight_iata: Optional[str] = Field(
        None, 
        description="IATA code of the flight"
    )
    flight_icao: Optional[str] = Field(
        None, 
        description="ICAO code of the flight"
    )
    flight_number: Optional[str] = Field(
        None, 
        description="Flight number"
    )
    airline_iata: Optional[str] = Field(
        None, 
        description="IATA code of the airline"
    )
    airline_icao: Optional[str] = Field(
        None, 
        description="ICAO code of the airline"
    )
    flight_status: Optional[str] = Field(
        None, 
        description="Flight status (scheduled, active, landed, cancelled, incident, diverted)"
    )
    dep_iata: Optional[str] = Field(
        None, 
        description="IATA code of departure airport"
    )
    dep_icao: Optional[str] = Field(
        None, 
        description="ICAO code of departure airport"
    )
    arr_iata: Optional[str] = Field(
        None, 
        description="IATA code of arrival airport"
    )
    arr_icao: Optional[str] = Field(
        None, 
        description="ICAO code of arrival airport"
    )
    min_delay_dep: Optional[int] = Field(
        None, 
        ge=0, 
        description="Minimum departure delay in minutes"
    )
    max_delay_dep: Optional[int] = Field(
        None, 
        ge=0, 
        description="Maximum departure delay in minutes"
    )
    min_delay_arr: Optional[int] = Field(
        None, 
        ge=0, 
        description="Minimum arrival delay in minutes"
    )
    max_delay_arr: Optional[int] = Field(
        None, 
        ge=0, 
        description="Maximum arrival delay in minutes"
    )
    flight_date: Optional[str] = Field(
        None, 
        description="Date in YYYY-MM-DD format (departure date)"
    )
    flight_date_from: Optional[str] = Field(
        None, 
        description="Start date in YYYY-MM-DD format (departure date range)"
    )
    flight_date_to: Optional[str] = Field(
        None, 
        description="End date in YYYY-MM-DD format (departure date range)"
    )
    arr_scheduled_time_from: Optional[str] = Field(
        None, 
        description="Start time in HH:MM format (scheduled arrival time range)"
    )
    arr_scheduled_time_to: Optional[str] = Field(
        None, 
        description="End time in HH:MM format (scheduled arrival time range)"
    )
    dep_scheduled_time_from: Optional[str] = Field(
        None, 
        description="Start time in HH:MM format (scheduled departure time range)"
    )
    dep_scheduled_time_to: Optional[str] = Field(
        None, 
        description="End time in HH:MM format (scheduled departure time range)"
    )
    arr_estimated_time_from: Optional[str] = Field(
        None, 
        description="Start time in HH:MM format (estimated arrival time range)"
    )
    arr_estimated_time_to: Optional[str] = Field(
        None, 
        description="End time in HH:MM format (estimated arrival time range)"
    )
    dep_estimated_time_from: Optional[str] = Field(
        None, 
        description="Start time in HH:MM format (estimated departure time range)"
    )
    dep_estimated_time_to: Optional[str] = Field(
        None, 
        description="End time in HH:MM format (estimated departure time range)"
    )
    limit: int = Field(
        100, 
        ge=1, 
        le=1000, 
        description="Number of records to return (1-1000)"
    )
    offset: int = Field(
        0, 
        ge=0, 
        description="Offset for pagination"
    )
    sort: str = Field(
        "flight_date", 
        description="Field to sort by (flight_date, dep_time, arr_time, dep_delay, arr_delay)"
    )
    
    @validator('flight_status')
    def validate_flight_status(cls, v):
        """Validate flight status."""
        if v and v not in ['scheduled', 'active', 'landed', 'cancelled', 'incident', 'diverted']:
            raise ValueError('Invalid flight status')
        return v
    
    @validator('sort')
    def validate_sort(cls, v):
        """Validate sort field."""
        valid_fields = ['flight_date', 'dep_time', 'arr_time', 'dep_delay', 'arr_delay']
        if v and v.lstrip('-') not in valid_fields:
            raise ValueError(f'Invalid sort field. Must be one of: {", ".join(valid_fields)}')
        return v

class AirportSearchParams(BaseModel):
    """Parameters for airport search."""
    search: Optional[str] = Field(
        None, 
        description="Search term for airport name, city, country, IATA, or ICAO code"
    )
    country_name: Optional[str] = Field(
        None, 
        description="Filter by country name"
    )
    country_iso2: Optional[str] = Field(
        None, 
        description="Filter by ISO 3166-1 alpha-2 country code"
    )
    city_iata_code: Optional[str] = Field(
        None, 
        description="Filter by IATA city code"
    )
    icao_code: Optional[str] = Field(
        None, 
        description="Filter by ICAO airport code"
    )
    iata_code: Optional[str] = Field(
        None, 
        description="Filter by IATA airport code"
    )
    timezone: Optional[str] = Field(
        None, 
        description="Filter by timezone (e.g., 'Australia/Sydney')"
    )
    limit: int = Field(
        100, 
        ge=1, 
        le=1000, 
        description="Number of records to return (1-1000)"
    )
    offset: int = Field(
        0, 
        ge=0, 
        description="Offset for pagination"
    )

class AviationStackClient(BaseApiClient):
    """Client for interacting with the AviationStack API."""
    
    def __init__(self, config: Optional[AviationStackConfig] = None):
        """Initialize the AviationStack client.
        
        Args:
            config: Configuration for the client. If not provided, will be loaded from environment.
        """
        config = config or AviationStackConfig()
        
        # Use access_key if provided, otherwise fall back to api_key
        api_key = config.access_key or config.api_key
        
        super().__init__(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            rate_limit=config.rate_limit
        )
        
        # Store config
        self.config = config
        
        # Initialize mock data provider
        self.mock_provider = MockDataProvider()
    
    async def get_flights(
        self,
        flight_iata: Optional[str] = None,
        flight_icao: Optional[str] = None,
        flight_number: Optional[str] = None,
        airline_iata: Optional[str] = None,
        airline_icao: Optional[str] = None,
        flight_status: Optional[str] = None,
        dep_iata: Optional[str] = None,
        dep_icao: Optional[str] = None,
        arr_iata: Optional[str] = None,
        arr_icao: Optional[str] = None,
        min_delay_dep: Optional[int] = None,
        max_delay_dep: Optional[int] = None,
        min_delay_arr: Optional[int] = None,
        max_delay_arr: Optional[int] = None,
        flight_date: Optional[str] = None,
        flight_date_from: Optional[str] = None,
        flight_date_to: Optional[str] = None,
        arr_scheduled_time_from: Optional[str] = None,
        arr_scheduled_time_to: Optional[str] = None,
        dep_scheduled_time_from: Optional[str] = None,
        dep_scheduled_time_to: Optional[str] = None,
        arr_estimated_time_from: Optional[str] = None,
        arr_estimated_time_to: Optional[str] = None,
        dep_estimated_time_from: Optional[str] = None,
        dep_estimated_time_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "flight_date",
        use_mock_fallback: bool = True
    ) -> Dict[str, Any]:
        """Search for flights.
        
        Args:
            flight_iata: IATA code of the flight
            flight_icao: ICAO code of the flight
            flight_number: Flight number
            airline_iata: IATA code of the airline
            airline_icao: ICAO code of the airline
            flight_status: Flight status (scheduled, active, landed, cancelled, incident, diverted)
            dep_iata: IATA code of departure airport
            dep_icao: ICAO code of departure airport
            arr_iata: IATA code of arrival airport
            arr_icao: ICAO code of arrival airport
            min_delay_dep: Minimum departure delay in minutes
            max_delay_dep: Maximum departure delay in minutes
            min_delay_arr: Minimum arrival delay in minutes
            max_delay_arr: Maximum arrival delay in minutes
            flight_date: Date in YYYY-MM-DD format (departure date)
            flight_date_from: Start date in YYYY-MM-DD format (departure date range)
            flight_date_to: End date in YYYY-MM-DD format (departure date range)
            arr_scheduled_time_from: Start time in HH:MM format (scheduled arrival time range)
            arr_scheduled_time_to: End time in HH:MM format (scheduled arrival time range)
            dep_scheduled_time_from: Start time in HH:MM format (scheduled departure time range)
            dep_scheduled_time_to: End time in HH:MM format (scheduled departure time range)
            arr_estimated_time_from: Start time in HH:MM format (estimated arrival time range)
            arr_estimated_time_to: End time in HH:MM format (estimated arrival time range)
            dep_estimated_time_from: Start time in HH:MM format (estimated departure time range)
            dep_estimated_time_to: End time in HH:MM format (estimated departure time range)
            limit: Number of records to return (1-1000)
            offset: Offset for pagination
            sort: Field to sort by (flight_date, dep_time, arr_time, dep_delay, arr_delay)
            use_mock_fallback: Whether to use mock data if the API call fails
            
        Returns:
            Dictionary containing flight data
        """
        # Validate input parameters
        params = FlightSearchParams(
            flight_iata=flight_iata,
            flight_icao=flight_icao,
            flight_number=flight_number,
            airline_iata=airline_iata,
            airline_icao=airline_icao,
            flight_status=flight_status,
            dep_iata=dep_iata,
            dep_icao=dep_icao,
            arr_iata=arr_iata,
            arr_icao=arr_icao,
            min_delay_dep=min_delay_dep,
            max_delay_dep=max_delay_dep,
            min_delay_arr=min_delay_arr,
            max_delay_arr=max_delay_arr,
            flight_date=flight_date,
            flight_date_from=flight_date_from,
            flight_date_to=flight_date_to,
            arr_scheduled_time_from=arr_scheduled_time_from,
            arr_scheduled_time_to=arr_scheduled_time_to,
            dep_scheduled_time_from=dep_scheduled_time_from,
            dep_scheduled_time_to=dep_scheduled_time_to,
            arr_estimated_time_from=arr_estimated_time_from,
            arr_estimated_time_to=arr_estimated_time_to,
            dep_estimated_time_from=dep_estimated_time_from,
            dep_estimated_time_to=dep_estimated_time_to,
            limit=limit,
            offset=offset,
            sort=sort
        )
        
        # Convert model to dict and remove None values
        query_params = {k: v for k, v in params.dict().items() if v is not None}
        
        try:
            # Make the API request
            response = await self._make_request(
                method="GET",
                endpoint="/flights",
                params=query_params,
                use_mock_fallback=use_mock_fallback
            )
            
            # Process the response
            if response and not response.get("is_mock", False):
                return self._process_flights_response(response)
                
            # If we get here, we're using mock data
            return response
            
        except Exception as e:
            logger.error(f"Error fetching flights: {str(e)}")
            if use_mock_fallback:
                logger.info("Falling back to mock data")
                return await self._get_mock_data("GET", "/flights", query_params, None)
            raise
    
    async def get_airports(
        self,
        search: Optional[str] = None,
        country_name: Optional[str] = None,
        country_iso2: Optional[str] = None,
        city_iata_code: Optional[str] = None,
        icao_code: Optional[str] = None,
        iata_code: Optional[str] = None,
        timezone: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        use_mock_fallback: bool = True
    ) -> Dict[str, Any]:
        """Search for airports.
        
        Args:
            search: Search term for airport name, city, country, IATA, or ICAO code
            country_name: Filter by country name
            country_iso2: Filter by ISO 3166-1 alpha-2 country code
            city_iata_code: Filter by IATA city code
            icao_code: Filter by ICAO airport code
            iata_code: Filter by IATA airport code
            timezone: Filter by timezone (e.g., 'Australia/Sydney')
            limit: Number of records to return (1-1000)
            offset: Offset for pagination
            use_mock_fallback: Whether to use mock data if the API call fails
            
        Returns:
            Dictionary containing airport data
        """
        # Validate input parameters
        params = AirportSearchParams(
            search=search,
            country_name=country_name,
            country_iso2=country_iso2,
            city_iata_code=city_iata_code,
            icao_code=icao_code,
            iata_code=iata_code,
            timezone=timezone,
            limit=limit,
            offset=offset
        )
        
        # Convert model to dict and remove None values
        query_params = {k: v for k, v in params.dict().items() if v is not None}
        
        try:
            # Make the API request
            response = await self._make_request(
                method="GET",
                endpoint="/airports",
                params=query_params,
                use_mock_fallback=use_mock_fallback
            )
            
            # Process the response
            if response and not response.get("is_mock", False):
                return self._process_airports_response(response)
                
            # If we get here, we're using mock data
            return response
            
        except Exception as e:
            logger.error(f"Error fetching airports: {str(e)}")
            if use_mock_fallback:
                logger.info("Falling back to mock data")
                return await self._get_mock_data("GET", "/airports", query_params, None)
            raise
    
    def _process_flights_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process the flights response from the API.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response in a standardized format
        """
        # This is a simplified example - actual implementation will depend on the API response format
        processed = {
            "data": [],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "count": 0,
                "total": 0
            },
            "is_mock": False
        }
        
        # Process flights
        if "data" in response and isinstance(response["data"], list):
            for flight in response["data"]:
                # Extract flight details
                flight_data = {
                    "flight_date": flight.get("flight_date"),
                    "flight_status": flight.get("flight_status"),
                    "departure": flight.get("departure", {}),
                    "arrival": flight.get("arrival", {}),
                    "airline": flight.get("airline", {}),
                    "flight": flight.get("flight", {}),
                    "aircraft": flight.get("aircraft"),
                    "live": flight.get("live"),
                    "codeshared": flight.get("codeshared"),
                    "is_mock": False
                }
                
                # Add to results
                processed["data"].append(flight_data)
        
        # Update pagination
        if "pagination" in response:
            processed["pagination"].update(response["pagination"])
        
        # Update count
        processed["pagination"]["count"] = len(processed["data"])
        
        return processed
    
    def _process_airports_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process the airports response from the API.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response in a standardized format
        """
        # This is a simplified example - actual implementation will depend on the API response format
        processed = {
            "data": [],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "count": 0,
                "total": 0
            },
            "is_mock": False
        }
        
        # Process airports
        if "data" in response and isinstance(response["data"], list):
            for airport in response["data"]:
                # Extract airport details
                airport_data = {
                    "id": airport.get("id"),
                    "iata_code": airport.get("iata_code"),
                    "icao_code": airport.get("icao_code"),
                    "name": airport.get("airport_name"),
                    "city": airport.get("city"),
                    "country": airport.get("country_name"),
                    "country_iso2": airport.get("country_iso2"),
                    "latitude": airport.get("latitude"),
                    "longitude": airport.get("longitude"),
                    "timezone": airport.get("timezone"),
                    "gmt": airport.get("gmt"),
                    "phone": airport.get("phone"),
                    "is_mock": False
                }
                
                # Add to results
                processed["data"].append(airport_data)
        
        # Update pagination
        if "pagination" in response:
            processed["pagination"].update(response["pagination"])
        
        # Update count
        processed["pagination"]["count"] = len(processed["data"])
        
        return processed
    
    async def _get_mock_data(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get mock data for the given request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            
        Returns:
            Mock response data
        """
        logger.info(f"Using mock data for {method} {endpoint}")
        
        # Handle different endpoints
        if endpoint == "/flights" and method.upper() == "GET":
            return self._get_mock_flights(params or {})
        elif endpoint == "/airports" and method.upper() == "GET":
            return self._get_mock_airports(params or {})
        
        # Default mock response
        return {
            "data": [],
            "pagination": {
                "limit": params.get("limit", 100) if params else 100,
                "offset": params.get("offset", 0) if params else 0,
                "count": 0,
                "total": 0
            },
            "is_mock": True
        }
    
    def _get_mock_flights(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock flight data.
        
        Args:
            params: Query parameters
            
        Returns:
            Mock flight data
        """
        # Parse parameters
        limit = min(int(params.get("limit", 100)), 1000)
        offset = max(int(params.get("offset", 0)), 0)
        
        # Get filter parameters
        dep_iata = params.get("dep_iata")
        arr_iata = params.get("arr_iata")
        flight_date = params.get("flight_date")
        flight_status = params.get("flight_status")
        
        # Generate mock flights
        flights = []
        num_flights = min(limit, 50)  # Max 50 mock flights
        
        for i in range(num_flights):
            # Generate random flight data
            flight = self.mock_provider._generate_mock_flight(
                dep_iata=dep_iata,
                arr_iata=arr_iata,
                flight_date=flight_date,
                flight_status=flight_status
            )
            
            if flight:
                flights.append(flight)
        
        # Create response
        return {
            "data": flights,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(flights),
                "total": len(flights) + offset
            },
            "is_mock": True
        }
    
    def _get_mock_airports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock airport data.
        
        Args:
            params: Query parameters
            
        Returns:
            Mock airport data
        """
        # Parse parameters
        limit = min(int(params.get("limit", 100)), 1000)
        offset = max(int(params.get("offset", 0)), 0)
        search = params.get("search", "").lower() if params.get("search") else None
        country_name = params.get("country_name", "").lower() if params.get("country_name") else None
        country_iso2 = params.get("country_iso2", "").upper() if params.get("country_iso2") else None
        city_iata_code = params.get("city_iata_code", "").upper() if params.get("city_iata_code") else None
        icao_code = params.get("icao_code", "").upper() if params.get("icao_code") else None
        iata_code = params.get("iata_code", "").upper() if params.get("iata_code") else None
        timezone = params.get("timezone")
        
        # Filter airports based on parameters
        filtered_airports = []
        
        for airport in self.mock_provider.AUSTRALIAN_AIRPORTS:
            # Apply filters
            if search and not any([
                search in airport["name"].lower(),
                search in airport["city"].lower(),
                search in airport["country"].lower(),
                search == airport["iata"].lower(),
                search == airport["icao"].lower() if airport["icao"] else False
            ]):
                continue
                
            if country_name and country_name != airport["country"].lower():
                continue
                
            if country_iso2 and country_iso2 != airport.get("country_code", ""):
                continue
                
            if city_iata_code and city_iata_code != airport.get("city_code", ""):
                continue
                
            if icao_code and icao_code != airport.get("icao", ""):
                continue
                
            if iata_code and iata_code != airport.get("iata", ""):
                continue
                
            if timezone and timezone != airport.get("timezone"):
                continue
            
            # Add airport to results
            filtered_airports.append({
                "id": airport.get("id", airport["iata"]),
                "iata_code": airport["iata"],
                "icao_code": airport.get("icao"),
                "airport_name": airport["name"],
                "city": airport["city"],
                "country_name": airport["country"],
                "country_iso2": airport.get("country_code", "AU"),
                "latitude": airport.get("lat"),
                "longitude": airport.get("lon"),
                "timezone": airport.get("timezone", "Australia/Sydney"),
                "gmt": airport.get("gmt", "+10:00"),
                "phone": airport.get("phone"),
                "is_mock": True
            })
        
        # Apply pagination
        total = len(filtered_airports)
        paginated_airports = filtered_airports[offset:offset+limit]
        
        # Create response
        return {
            "data": paginated_airports,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(paginated_airports),
                "total": total
            },
            "is_mock": True
        }
