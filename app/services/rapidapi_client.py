"""
RapidAPI client for fetching flight data.

This module provides a client for interacting with flight data APIs available on RapidAPI,
such as Skyscanner, Aviasales, and others.
"""
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union

from pydantic import BaseModel, HttpUrl, Field

from .base_client import BaseApiClient, ApiClientError
from .config import RapidApiConfig
from .mock_data_provider import MockDataProvider

# Configure logging
logger = logging.getLogger(__name__)

# Models for request/response validation
class FlightSearchParams(BaseModel):
    """Parameters for flight search."""
    origin: str = Field(..., description="Origin IATA code")
    destination: str = Field(..., description="Destination IATA code")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format")
    adults: int = Field(1, ge=1, le=9, description="Number of adult passengers")
    children: int = Field(0, ge=0, le=8, description="Number of child passengers")
    infants: int = Field(0, ge=0, le=8, description="Number of infant passengers")
    travel_class: str = Field("ECONOMY", description="Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)")
    non_stop: bool = Field(False, description="Only show non-stop flights")
    currency: str = Field("AUD", description="Currency code")
    market: str = Field("AU", description="Market/country code")
    locale: str = Field("en-AU", description="Locale for results")

class RapidApiClient(BaseApiClient):
    """Client for interacting with flight data APIs on RapidAPI."""
    
    def __init__(self, config: Optional[RapidApiConfig] = None):
        """Initialize the RapidAPI client.
        
        Args:
            config: Configuration for the client. If not provided, will be loaded from environment.
        """
        config = config or RapidApiConfig()
        super().__init__(
            api_key=config.api_key,
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
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        travel_class: str = "ECONOMY",
        non_stop: bool = False,
        currency: str = "AUD",
        market: str = "AU",
        locale: str = "en-AU",
        use_mock_fallback: bool = True
    ) -> Dict[str, Any]:
        """Search for flights.
        
        Args:
            origin: Origin IATA code (e.g., "SYD")
            destination: Destination IATA code (e.g., "MEL")
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (for round-trip)
            adults: Number of adult passengers (1-9)
            children: Number of child passengers (0-8)
            infants: Number of infant passengers (0-8)
            travel_class: Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            non_stop: If true, only return non-stop flights
            currency: Currency code (default: AUD)
            market: Market/country code (default: AU)
            locale: Locale for results (default: en-AU)
            use_mock_fallback: Whether to use mock data if the API call fails
            
        Returns:
            Dictionary containing flight search results
        """
        # Validate input parameters
        params = FlightSearchParams(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            travel_class=travel_class,
            non_stop=non_stop,
            currency=currency,
            market=market,
            locale=locale
        )
        
        # Build query parameters
        query_params = {
            "adults": params.adults,
            "origin": params.origin,
            "destination": params.destination,
            "departureDate": params.departure_date,
            "currency": params.currency,
            "market": params.market,
            "locale": params.locale
        }
        
        if params.return_date:
            query_params["returnDate"] = params.return_date
            
        if params.children > 0:
            query_params["children"] = params.children
            
        if params.infants > 0:
            query_params["infants"] = params.infants
            
        if params.travel_class != "ECONOMY":
            query_params["cabinClass"] = params.travel_class.lower()
            
        if params.non_stop:
            query_params["stops"] = "0"
        
        try:
            # Make the API request
            response = await self._make_request(
                method="GET",
                endpoint="/search",
                params=query_params,
                use_mock_fallback=use_mock_fallback
            )
            
            # Process the response
            if response and not response.get("is_mock", False):
                return self._process_flight_search_response(response)
                
            # If we get here, we're using mock data
            return response
            
        except Exception as e:
            logger.error(f"Error searching flights: {str(e)}")
            if use_mock_fallback:
                logger.info("Falling back to mock data")
                return await self._get_mock_data(
                    "GET", 
                    "/search", 
                    query_params, 
                    None
                )
            raise
    
    def _process_flight_search_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process the flight search response from the API.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response in a standardized format
        """
        # This is a simplified example - actual implementation will depend on the API response format
        processed = {
            "data": [],
            "meta": {
                "count": 0,
                "links": {}
            },
            "dictionaries": {
                "carriers": {},
                "aircraft": {},
                "locations": {}
            },
            "is_mock": False
        }
        
        # Process itineraries
        if "itineraries" in response:
            for itinerary in response["itineraries"][:10]:  # Limit to 10 results
                # Extract segments
                segments = []
                for segment in itinerary.get("segments", []):
                    carrier_code = segment.get("carrierCode")
                    segments.append({
                        "id": segment.get("id"),
                        "departure": segment.get("departure"),
                        "arrival": segment.get("arrival"),
                        "carrierCode": carrier_code,
                        "number": segment.get("number"),
                        "aircraft": segment.get("aircraft", {}).get("code"),
                        "duration": segment.get("duration"),
                        "stops": segment.get("numberOfStops", 0)
                    })
                    
                    # Add to dictionaries
                    if carrier_code and carrier_code not in processed["dictionaries"]["carriers"]:
                        processed["dictionaries"]["carriers"][carrier_code] = carrier_code
                    
                    # Add locations
                    for loc in ["departure", "arrival"]:
                        if loc in segment and "iataCode" in segment[loc]:
                            iata = segment[loc]["iataCode"]
                            if iata not in processed["dictionaries"]["locations"]:
                                processed["dictionaries"]["locations"][iata] = {
                                    "cityCode": iata[:3],
                                    "countryCode": "AU"  # Default to AU
                                }
                
                # Add pricing info if available
                price_info = itinerary.get("price", {})
                
                # Add to results
                processed["data"].append({
                    "type": "flight-offer",
                    "id": itinerary.get("id"),
                    "source": "RapidAPI",
                    "instantTicketingRequired": False,
                    "nonHomogeneous": False,
                    "oneWay": not bool(itinerary.get("returnDate")),
                    "lastTicketingDate": "2099-12-31",  # Default far future date
                    "numberOfBookableSeats": 9,  # Default value
                    "itineraries": [{
                        "duration": f"PT{random.randint(60, 240)}M",  # Random duration
                        "segments": segments
                    }],
                    "price": {
                        "currency": price_info.get("currency", "AUD"),
                        "total": price_info.get("total"),
                        "base": price_info.get("base"),
                        "fees": [],
                        "grandTotal": price_info.get("total")
                    },
                    "pricingOptions": {
                        "fareType": ["PUBLISHED"],
                        "includedCheckedBagsOnly": True
                    },
                    "validatingAirlineCodes": [segments[0]["carrierCode"]] if segments else [],
                    "travelerPricings": [
                        {
                            "travelerId": "1",
                            "fareOption": "STANDARD",
                            "travelerType": "ADULT",
                            "price": {
                                "currency": price_info.get("currency", "AUD"),
                                "total": price_info.get("total"),
                                "base": price_info.get("base", price_info.get("total", 0) * 0.7)
                            },
                            "fareDetailsBySegment": [
                                {
                                    "segmentId": segments[0]["id"] if segments else "1",
                                    "cabin": itinerary.get("cabinClass", "ECONOMY"),
                                    "fareBasis": "Y",
                                    "class": "Y",
                                    "includedCheckedBags": {
                                        "quantity": 1
                                    }
                                }
                            ]
                        }
                    ] if price_info else []
                })
        
        # Update count
        processed["meta"]["count"] = len(processed["data"])
        
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
        if endpoint == "/search" and method.upper() == "GET":
            return self._get_mock_flight_search(params or {})
        
        # Default mock response
        return {
            "data": [],
            "meta": {
                "count": 0,
                "links": {}
            },
            "dictionaries": {
                "carriers": {},
                "aircraft": {},
                "locations": {}
            },
            "is_mock": True
        }
    
    def _get_mock_flight_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock flight search results.
        
        Args:
            params: Search parameters
            
        Returns:
            Mock flight search results
        """
        # Parse parameters
        origin = params.get("origin", "SYD")
        destination = params.get("destination", "MEL")
        departure_date = params.get("departureDate")
        return_date = params.get("returnDate")
        adults = int(params.get("adults", 1))
        children = int(params.get("children", 0))
        infants = int(params.get("infants", 0))
        travel_class = params.get("cabinClass", "economy").upper()
        currency = params.get("currency", "AUD")
        
        # Generate mock flights
        flights = []
        num_flights = random.randint(3, 10)  # 3-10 mock flights
        
        for i in range(num_flights):
            # Generate random departure time (morning, afternoon, evening)
            hour = random.choice([7, 10, 13, 16, 19, 21])
            minute = random.choice([0, 15, 30, 45])
            
            # Generate random flight duration (1-6 hours)
            duration_hours = random.randint(1, 6)
            duration_minutes = random.randint(0, 59)
            
            # Create departure and arrival times
            departure_time = datetime.strptime(f"{departure_date} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
            arrival_time = departure_time + timedelta(hours=duration_hours, minutes=duration_minutes)
            
            # Select random airline and aircraft
            airline = random.choice(self.mock_provider.AIRLINES)
            aircraft = random.choice(self.mock_provider.AIRCRAFT_TYPES)
            
            # Generate random price based on class and route
            base_price = random.uniform(100, 500)
            if travel_class == "BUSINESS":
                base_price *= 2.5
            elif travel_class == "FIRST":
                base_price *= 4.0
                
            # Add some randomness
            price = round(base_price * random.uniform(0.9, 1.5), 2)
            
            # Generate flight number
            flight_number = f"{airline['iata']}{random.randint(100, 9999)}"
            
            # Create flight segments
            segments = [{
                "id": str(uuid.uuid4()),
                "departure": {
                    "iataCode": origin,
                    "at": departure_time.strftime("%Y-%m-%dT%H:%M:%S")
                },
                "arrival": {
                    "iataCode": destination,
                    "at": arrival_time.strftime("%Y-%m-%dT%H:%M:%S")
                },
                "carrierCode": airline["iata"],
                "number": flight_number,
                "aircraft": {
                    "code": aircraft["code"]
                },
                "duration": f"PT{duration_hours}H{duration_minutes}M",
                "numberOfStops": 0,
                "blacklistedInEU": False
            }]
            
            # Create return segment if round-trip
            if return_date:
                return_hour = random.choice([9, 12, 15, 18, 20])
                return_minute = random.choice([0, 15, 30, 45])
                
                return_departure = datetime.strptime(f"{return_date} {return_hour:02d}:{return_minute:02d}", "%Y-%m-%d %H:%M")
                return_arrival = return_departure + timedelta(hours=duration_hours, minutes=duration_minutes)
                
                segments.append({
                    "id": str(uuid.uuid4()),
                    "departure": {
                        "iataCode": destination,
                        "at": return_departure.strftime("%Y-%m-%dT%H:%M:%S")
                    },
                    "arrival": {
                        "iataCode": origin,
                        "at": return_arrival.strftime("%Y-%m-%dT%H:%M:%S")
                    },
                    "carrierCode": airline["iata"],
                    "number": f"{airline['iata']}{random.randint(100, 9999)}",
                    "aircraft": {
                        "code": aircraft["code"]
                    },
                    "duration": f"PT{duration_hours}H{duration_minutes}M",
                    "numberOfStops": 0,
                    "blacklistedInEU": False
                })
            
            # Calculate total price for all passengers
            total_price = price * (adults + children * 0.75 + infants * 0.1)
            
            # Create flight offer
            flights.append({
                "type": "flight-offer",
                "id": str(uuid.uuid4()),
                "source": "MOCK",
                "instantTicketingRequired": False,
                "nonHomogeneous": False,
                "oneWay": not bool(return_date),
                "lastTicketingDate": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "numberOfBookableSeats": 9,
                "itineraries": [{
                    "duration": f"PT{duration_hours}H{duration_minutes}M",
                    "segments": segments
                }],
                "price": {
                    "currency": currency,
                    "total": f"{total_price:.2f}",
                    "base": f"{price * (adults + children * 0.75):.2f}",
                    "fees": [
                        {
                            "amount": "0.00",
                            "type": "SUPPLIER"
                        },
                        {
                            "amount": "0.00",
                            "type": "TICKETING"
                        }
                    ],
                    "grandTotal": f"{total_price:.2f}"
                },
                "pricingOptions": {
                    "fareType": ["PUBLISHED"],
                    "includedCheckedBagsOnly": True
                },
                "validatingAirlineCodes": [airline["iata"]],
                "travelerPricings": [
                    {
                        "travelerId": "1",
                        "fareOption": "STANDARD",
                        "travelerType": "ADULT",
                        "price": {
                            "currency": currency,
                            "total": f"{price:.2f}",
                            "base": f"{price * 0.7:.2f}"
                        },
                        "fareDetailsBySegment": [
                            {
                                "segmentId": segments[0]["id"],
                                "cabin": travel_class,
                                "fareBasis": "Y",
                                "class": "Y",
                                "includedCheckedBags": {
                                    "quantity": 1
                                }
                            }
                        ]
                    }
                ]
            })
        
        # Create response
        return {
            "data": flights,
            "meta": {
                "count": len(flights),
                "links": {
                    "self": f"{self.base_url}/search"
                }
            },
            "dictionaries": {
                "carriers": {
                    airline["iata"]: airline["name"] 
                    for airline in self.mock_provider.AIRLINES
                },
                "aircraft": {
                    ac["code"]: ac["name"]
                    for ac in self.mock_provider.AIRCRAFT_TYPES
                },
                "locations": {
                    origin: {"cityCode": origin[:3], "countryCode": "AU"},
                    destination: {"cityCode": destination[:3], "countryCode": "AU"}
                }
            },
            "is_mock": True
        }
