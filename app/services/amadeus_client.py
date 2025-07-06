"""
Amadeus API client for fetching flight data.

This module provides a client for interacting with the Amadeus Self-Service APIs.
It handles authentication, request formatting, and response parsing.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import httpx
from fastapi import HTTPException

from app.core.config import settings
from .mock_data_provider import MockDataProvider

# Configure logging
logger = logging.getLogger(__name__)

class AmadeusClientError(Exception):
    """Custom exception for Amadeus API errors."""
    pass

class AmadeusClient:
    """Client for interacting with Amadeus Self-Service APIs."""
    
    BASE_URL = "https://test.api.amadeus.com"  # Test environment
    # BASE_URL = "https://api.amadeus.com"  # Production environment
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize the Amadeus client with API credentials.
        
        Args:
            api_key: Amadeus API key (client ID)
            api_secret: Amadeus API secret (client secret)
        """
        self.api_key = api_key or settings.AMADEUS_API_KEY
        self.api_secret = api_secret or settings.AMADEUS_API_SECRET
        self.access_token = None
        self.token_expiry = None
        self.session = httpx.AsyncClient(timeout=30.0)
        self.mock_provider = MockDataProvider()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.aclose()
    
    async def _get_access_token(self) -> str:
        """Get an OAuth2 access token from Amadeus.
        
        Returns:
            str: Access token
            
        Raises:
            AmadeusClientError: If authentication fails
        """
        # Check if we have a valid token
        if self.access_token and self.token_expiry and self.token_expiry > datetime.utcnow() + timedelta(minutes=5):
            return self.access_token
        
        # Request a new token
        auth_url = f"{self.BASE_URL}/v1/security/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            response = await self.session.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            self.token_expiry = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            
            return self.access_token
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Amadeus authentication failed: {e.response.text}"
            logger.error(error_msg)
            raise AmadeusClientError(error_msg) from e
        except Exception as e:
            error_msg = f"Error during Amadeus authentication: {str(e)}"
            logger.error(error_msg)
            raise AmadeusClientError(error_msg) from e
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_mock_fallback: bool = True
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Amadeus API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body (for POST/PUT)
            use_mock_fallback: Whether to fall back to mock data on failure
            
        Returns:
            API response data as a dictionary
            
        Raises:
            AmadeusClientError: If the request fails and no fallback is available
        """
        if not self.api_key or not self.api_secret:
            if use_mock_fallback:
                logger.warning("Amadeus API credentials not configured, using mock data")
                return {}
            raise AmadeusClientError("Amadeus API credentials not configured")
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {await self._get_access_token()}",
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = await self.session.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await self.session.post(url, params=params, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Amadeus API request failed ({e.response.status_code}): {e.response.text}"
            logger.error(error_msg)
            
            if use_mock_fallback:
                logger.info("Falling back to mock data")
                return {}
                
            raise AmadeusClientError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Error during Amadeus API request: {str(e)}"
            logger.error(error_msg)
            
            if use_mock_fallback:
                logger.info("Falling back to mock data")
                return {}
                
            raise AmadeusClientError(error_msg) from e
    
    async def get_flight_offers(
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
        max_price: Optional[int] = None,
        currency: str = "AUD",
        include_airlines: Optional[List[str]] = None,
        exclude_airlines: Optional[List[str]] = None,
        use_mock_fallback: bool = True
    ) -> Dict[str, Any]:
        """Search for flight offers using Amadeus Flight Offers Search API.
        
        Args:
            origin: Origin airport/city IATA code (e.g., "SYD")
            destination: Destination airport/city IATA code (e.g., "MEL")
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (for round-trip)
            adults: Number of adult passengers (1-9)
            children: Number of child passengers (0-9)
            infants: Number of infant passengers (0-9)
            travel_class: Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            non_stop: If true, only return non-stop flights
            max_price: Maximum price per traveler
            currency: Currency code (default: AUD)
            include_airlines: List of airline IATA codes to include
            exclude_airlines: List of airline IATA codes to exclude
            use_mock_fallback: Whether to fall back to mock data on failure
            
        Returns:
            Dictionary containing flight offers
        """
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": currency,
            "max": 10,  # Max number of results
        }
        
        if return_date:
            params["returnDate"] = return_date
        
        if children > 0:
            params["children"] = children
        
        if infants > 0:
            params["infants"] = infants
        
        if travel_class != "ECONOMY":
            params["travelClass"] = travel_class
        
        if non_stop:
            params["nonStop"] = "true"
        
        if max_price:
            params["maxPrice"] = max_price
        
        if include_airlines:
            params["includedAirlineCodes"] = ",".join(include_airlines)
        
        if exclude_airlines:
            params["excludedAirlineCodes"] = ",".join(exclude_airlines)
        
        # Make the API request
        response = await self._make_request(
            "GET",
            "/v2/shopping/flight-offers",
            params=params,
            use_mock_fallback=use_mock_fallback
        )
        
        # If response is empty (and we're using mock fallback), generate mock data
        if not response and use_mock_fallback:
            logger.info("Using mock data for flight offers")
            # Convert date string to datetime for mock provider
            departure_dt = datetime.strptime(departure_date, "%Y-%m-%d")
            return_dt = datetime.strptime(return_date, "%Y-%m-%d") if return_date else None
            
            # Generate mock flights
            flights = self.mock_provider.get_flights(
                origin=origin,
                destination=destination,
                date_from=departure_dt,
                date_to=return_dt or (departure_dt + timedelta(days=1)),
                limit=10
            )
            
            # Format to match Amadeus response structure
            return {
                "meta": {
                    "count": len(flights),
                    "links": {"self": ""}
                },
                "data": [
                    self._format_mock_flight_offer(flight)
                    for flight in flights
                ],
                "dictionaries": {
                    "carriers": {
                        flight["airline"]["iata"]: flight["airline"]["name"]
                        for flight in flights
                    },
                    "aircraft": {
                        flight["aircraft"]["code"]: flight["aircraft"]["name"]
                        for flight in flights
                    },
                    "locations": {
                        origin: {"cityCode": origin, "countryCode": "AU"},
                        destination: {"cityCode": destination, "countryCode": "AU"}
                    }
                },
                "warnings": ["Mock data used - Amadeus API not available"],
                "is_mock": True
            }
        
        return response
    
    def _format_mock_flight_offer(self, flight: Dict[str, Any]) -> Dict[str, Any]:
        """Format a mock flight into Amadeus flight offer format."""
        departure_time = datetime.fromisoformat(flight["departure_time"])
        arrival_time = datetime.fromisoformat(flight["arrival_time"])
        
        return {
            "type": "flight-offer",
            "id": flight["id"],
            "source": "MOCK",
            "instantTicketingRequired": False,
            "nonHomogeneous": False,
            "oneWay": True,  # For simplicity, we'll treat all as one-way
            "lastTicketingDate": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "numberOfBookableSeats": flight["available_seats"],
            "itineraries": [
                {
                    "duration": f"PT{flight['duration']}M",
                    "segments": [
                        {
                            "departure": {
                                "iataCode": flight["origin"]["iata"],
                                "terminal": str(random.randint(1, 3)),
                                "at": departure_time.strftime("%Y-%m-%dT%H:%M:%S")
                            },
                            "arrival": {
                                "iataCode": flight["destination"]["iata"],
                                "terminal": str(random.randint(1, 3)),
                                "at": arrival_time.strftime("%Y-%m-%dT%H:%M:%S")
                            },
                            "carrierCode": flight["airline"]["iata"],
                            "number": flight["flight_number"][-4:],
                            "aircraft": {
                                "code": flight["aircraft"]["code"]
                            },
                            "operating": {
                                "carrierCode": flight["airline"]["iata"]
                            },
                            "duration": f"PT{flight['duration']}M",
                            "id": str(uuid.uuid4()),
                            "numberOfStops": 0,
                            "blacklistedInEU": False
                        }
                    ]
                }
            ],
            "price": {
                "currency": flight["currency"],
                "total": str(flight["price"]),
                "base": str(round(flight["price"] * 0.7, 2)),
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
                "grandTotal": str(flight["price"])
            },
            "pricingOptions": {
                "fareType": ["PUBLISHED"],
                "includedCheckedBagsOnly": True
            },
            "validatingAirlineCodes": [flight["airline"]["iata"]],
            "travelerPricings": [
                {
                    "travelerId": "1",
                    "fareOption": "STANDARD",
                    "travelerType": "ADULT",
                    "price": {
                        "currency": flight["currency"],
                        "total": str(flight["price"]),
                        "base": str(round(flight["price"] * 0.7, 2))
                    },
                    "fareDetailsBySegment": [
                        {
                            "segmentId": "1",
                            "cabin": "ECONOMY",
                            "fareBasis": "Y",
                            "class": "Y",
                            "includedCheckedBags": {
                                "quantity": 1
                            }
                        }
                    ]
                }
            ]
        }
    
    async def get_flight_most_traveled_destinations(
        self,
        origin_city_code: str,
        period: str = "2023-01",
        max_destinations: int = 5,
        use_mock_fallback: bool = True
    ) -> Dict[str, Any]:
        """Get most traveled destinations from a city using Amadeus Travel Analytics API.
        
        Args:
            origin_city_code: IATA code of the origin city
            period: Period in YYYY-MM format (default: current month)
            max_destinations: Maximum number of destinations to return
            use_mock_fallback: Whether to fall back to mock data on failure
            
        Returns:
            Dictionary containing most traveled destinations
        """
        params = {
            "originCityCode": origin_city_code,
            "period": period,
            "max": max_destinations
        }
        
        # Make the API request
        response = await self._make_request(
            "GET",
            "/v1/analytics/itinerary-price-metrics",
            params=params,
            use_mock_fallback=use_mock_fallback
        )
        
        # If response is empty (and we're using mock fallback), generate mock data
        if not response and use_mock_fallback:
            logger.info("Using mock data for most traveled destinations")
            
            # Get all airports except the origin
            airports = [a for a in self.mock_provider.get_airports() if a["iata"] != origin_city_code]
            
            # Take a random sample of destinations
            num_destinations = min(max_destinations, len(airports))
            destinations = random.sample(airports, num_destinations)
            
            # Generate mock data
            data = []
            for i, dest in enumerate(destinations):
                # Generate random metrics with some variation
                travelers = random.randint(500, 5000)
                average_price = random.uniform(100, 1000)
                
                data.append({
                    "destination": dest["iata"],
                    "analytics": {
                        "travelers": {
                            "score": round(1.0 - (i * 0.1), 2),  # Decreasing score
                            "value": travelers
                        },
                        "price": {
                            "score": round(0.5 + (random.random() * 0.5), 2),  # 0.5-1.0
                            "value": round(average_price, 2),
                            "currency": "AUD"
                        },
                        "flightOffers": random.randint(5, 50)
                    }
                })
            
            return {
                "meta": {
                    "count": len(data),
                    "links": {"self": ""}
                },
                "data": data,
                "warnings": ["Mock data used - Amadeus API not available"],
                "is_mock": True
            }
        
        return response
