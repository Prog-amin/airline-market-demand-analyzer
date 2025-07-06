"""
Configuration for API clients.

This module provides configuration classes for different API clients used in the application.
"""
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseSettings, Field, validator, HttpUrl
from enum import Enum

class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class BaseApiConfig(BaseSettings):
    """Base configuration for API clients."""
    
    # API Settings
    api_key: Optional[str] = Field(
        None, 
        env="API_KEY",
        description="API key for authentication"
    )
    api_secret: Optional[str] = Field(
        None, 
        env="API_SECRET",
        description="API secret for authentication"
    )
    base_url: str = Field(
        ..., 
        env="API_BASE_URL",
        description="Base URL for the API"
    )
    
    # Request Settings
    timeout: float = Field(
        30.0,
        env="API_TIMEOUT",
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        3,
        env="API_MAX_RETRIES",
        description="Maximum number of retries for failed requests"
    )
    retry_delay: float = Field(
        1.0,
        env="API_RETRY_DELAY",
        description="Initial delay between retries in seconds"
    )
    
    # Rate Limiting
    rate_limit_requests: Optional[int] = Field(
        None,
        env="API_RATE_LIMIT_REQUESTS",
        description="Number of requests allowed in the rate limit window"
    )
    rate_limit_seconds: Optional[int] = Field(
        None,
        env="API_RATE_LIMIT_SECONDS",
        description="Length of the rate limit window in seconds"
    )
    
    # Logging
    log_level: LogLevel = Field(
        LogLevel.INFO,
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    # Environment
    environment: Environment = Field(
        Environment.DEVELOPMENT,
        env="ENVIRONMENT",
        description="Application environment"
    )
    
    # Mocking
    use_mock: bool = Field(
        False,
        env="USE_MOCK",
        description="Whether to use mock data instead of making real API calls"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    @property
    def rate_limit(self) -> Optional[Tuple[int, int]]:
        """Get the rate limit as a tuple of (requests, seconds)."""
        if self.rate_limit_requests and self.rate_limit_seconds:
            return (self.rate_limit_requests, self.rate_limit_seconds)
        return None
    
    @validator('base_url')
    def validate_base_url(cls, v):
        """Ensure base URL ends with a trailing slash."""
        if v and not v.endswith('/'):
            return f"{v}/"
        return v
    
    def get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        headers = {
            "Accept": "application/json",
            "User-Agent": f"AirlineMarketApp/1.0 ({self.environment})"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers

class AmadeusConfig(BaseApiConfig):
    """Configuration for the Amadeus API client."""
    
    class Config:
        env_prefix = "AMADEUS_"
    
    # Override default base URL for Amadeus
    base_url: str = Field(
        "https://test.api.amadeus.com",  # Test environment
        # "https://api.amadeus.com",  # Production environment
        env=["AMADEUS_BASE_URL", "API_BASE_URL"],
        description="Base URL for the Amadeus API"
    )
    
    # Amadeus-specific settings
    auth_url: str = Field(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        env="AMADEUS_AUTH_URL",
        description="URL for OAuth2 token endpoint"
    )
    
    # Rate limiting (Amadeus has different rate limits for different endpoints)
    default_rate_limit_requests: int = 20
    default_rate_limit_seconds: int = 1  # Per second
    
    def get_endpoint_rate_limit(self, endpoint: str) -> Tuple[int, int]:
        """Get rate limit for a specific endpoint.
        
        Amadeus has different rate limits for different endpoints.
        This method returns the appropriate rate limit based on the endpoint.
        """
        # Define rate limits for specific endpoints
        endpoint_limits = {
            "/v2/shopping/flight-offers": (10, 1),  # 10 requests per second
            "/v1/analytics/itinerary-price-metrics": (5, 1),  # 5 requests per second
            "/v1/booking/flight-orders": (20, 1),  # 20 requests per second
        }
        
        # Find the most specific matching endpoint
        for path, limit in endpoint_limits.items():
            if endpoint.startswith(path):
                return limit
                
        # Default rate limit
        return (self.default_rate_limit_requests, self.default_rate_limit_seconds)

class RapidApiConfig(BaseApiConfig):
    """Configuration for the RapidAPI client."""
    
    class Config:
        env_prefix = "RAPIDAPI_"
    
    # Override default base URL for RapidAPI
    base_url: str = Field(
        "https://skyscanner44.p.rapidapi.com",
        env=["RAPIDAPI_BASE_URL", "API_BASE_URL"],
        description="Base URL for the RapidAPI endpoint"
    )
    
    # RapidAPI requires the API key in the headers
    api_host: str = Field(
        "skyscanner44.p.rapidapi.com",
        env="RAPIDAPI_HOST",
        description="RapidAPI host"
    )
    
    # Rate limiting (RapidAPI typically has per-minute limits)
    default_rate_limit_requests: int = 50
    default_rate_limit_seconds: int = 60  # Per minute
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for RapidAPI requests."""
        headers = super().get_headers()
        
        # RapidAPI requires these headers
        if self.api_key:
            headers.update({
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            })
            
        return headers

class AviationStackConfig(BaseApiConfig):
    """Configuration for the AviationStack API client."""
    
    class Config:
        env_prefix = "AVIATIONSTACK_"
    
    # Override default base URL for AviationStack
    base_url: str = Field(
        "http://api.aviationstack.com/v1",
        env=["AVIATIONSTACK_BASE_URL", "API_BASE_URL"],
        description="Base URL for the AviationStack API"
    )
    
    # AviationStack uses access_key as the parameter name for the API key
    access_key: Optional[str] = Field(
        None,
        env="AVIATIONSTACK_ACCESS_KEY",
        description="Access key for the AviationStack API"
    )
    
    # Rate limiting (AviationStack has different tiers)
    default_rate_limit_requests: int = 500
    default_rate_limit_seconds: int = 3600  # Per hour (free tier)
    
    def get_params(self, **kwargs) -> Dict[str, str]:
        """Get default query parameters for API requests."""
        params = {}
        
        # Add access key to all requests
        if self.access_key:
            params["access_key"] = self.access_key
        elif self.api_key:
            # Fall back to api_key if access_key is not set
            params["access_key"] = self.api_key
            
        # Add any additional parameters
        params.update(kwargs)
        return params

def get_config(provider: str = "amadeus") -> BaseApiConfig:
    """Get configuration for the specified provider.
    
    Args:
        provider: Name of the provider (amadeus, rapidapi, aviationstack)
        
    Returns:
        Configuration object for the specified provider
        
    Raises:
        ValueError: If an invalid provider is specified
    """
    providers = {
        "amadeus": AmadeusConfig,
        "rapidapi": RapidApiConfig,
        "aviationstack": AviationStackConfig
    }
    
    if provider not in providers:
        raise ValueError(f"Invalid provider: {provider}. Must be one of: {', '.join(providers.keys())}")
    
    return providers[provider]()
