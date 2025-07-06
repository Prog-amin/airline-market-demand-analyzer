"""
Base client class for API clients.

This module provides a base class that can be extended by specific API clients
like Amadeus, RapidAPI, etc. It handles common functionality like request
retries, error handling, and response formatting.
"""
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Type, Generic, Union, Callable

import httpx
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic typing
T = TypeVar('T', bound=BaseModel)
ResponseType = Union[Dict[str, Any], List[Dict[str, Any]]]

class ApiClientError(Exception):
    """Base exception for API client errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class RateLimitExceededError(ApiClientError):
    """Raised when the API rate limit is exceeded."""
    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        message = "API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message=message, **kwargs)

class BaseApiClient(ABC):
    """Base class for API clients with common functionality."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit: Optional[Tuple[int, int]] = None  # (requests, seconds)
    ):
        """Initialize the base API client.
        
        Args:
            api_key: API key for authentication
            api_secret: API secret for authentication (if required)
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries in seconds (will be doubled on each retry)
            rate_limit: Optional rate limit as a tuple of (requests, seconds)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/') if base_url else None
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit
        
        # Rate limiting state
        self.rate_limit_remaining = rate_limit[0] if rate_limit else None
        self.rate_limit_reset = None
        self.last_request_time = None
        
        # Create a client session
        self.session = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close the session."""
        await self.close()
    
    async def close(self):
        """Close the HTTP session."""
        if hasattr(self, 'session') and self.session:
            await self.session.aclose()
    
    async def _check_rate_limit(self):
        """Check if we've hit the rate limit and wait if necessary."""
        if not self.rate_limit or not self.rate_limit_remaining:
            return
            
        current_time = time.time()
        
        # Check if we need to wait for rate limit reset
        if self.rate_limit_reset and current_time < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - current_time
            logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
        
        # Reset rate limit counter if the window has passed
        if self.rate_limit_reset and current_time >= self.rate_limit_reset:
            self.rate_limit_remaining = self.rate_limit[0]
    
    def _update_rate_limit_headers(self, headers: Dict[str, str]):
        """Update rate limit state from response headers."""
        if not self.rate_limit:
            return
            
        # Update rate limit state from standard headers
        remaining = headers.get('X-RateLimit-Remaining')
        reset_time = headers.get('X-RateLimit-Reset')
        
        if remaining is not None:
            try:
                self.rate_limit_remaining = int(remaining)
            except (ValueError, TypeError):
                pass
                
        if reset_time is not None:
            try:
                self.rate_limit_reset = int(reset_time)
            except (ValueError, TypeError):
                pass
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        model: Optional[Type[T]] = None,
        use_mock_fallback: bool = True
    ) -> Union[Dict[str, Any], T]:
        """Make an HTTP request with retries and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body (for POST/PUT)
            headers: Additional headers
            model: Pydantic model to validate response against
            use_mock_fallback: Whether to use mock data on failure
            
        Returns:
            Parsed JSON response or model instance
            
        Raises:
            ApiClientError: If the request fails and no fallback is available
        """
        # Ensure endpoint starts with a slash
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'
            
        url = f"{self.base_url}{endpoint}"
        headers = headers or {}
        
        # Add authentication headers if needed
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
            
        # Add content type for POST/PUT requests
        if method.upper() in ('POST', 'PUT', 'PATCH') and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        
        # Initialize retry state
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Check rate limits before making the request
                await self._check_rate_limit()
                
                # Make the request
                self.last_request_time = time.time()
                
                logger.debug(f"Making {method} request to {url} (attempt {retry_count + 1}/{self.max_retries + 1})")
                
                if method.upper() == 'GET':
                    response = await self.session.get(url, params=params, headers=headers)
                elif method.upper() == 'POST':
                    response = await self.session.post(url, json=data, params=params, headers=headers)
                elif method.upper() == 'PUT':
                    response = await self.session.put(url, json=data, params=params, headers=headers)
                elif method.upper() == 'DELETE':
                    response = await self.session.delete(url, params=params, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Update rate limit state from response headers
                self._update_rate_limit_headers(dict(response.headers))
                
                # Handle error responses
                if response.status_code >= 400:
                    error_msg = f"API request failed with status {response.status_code}"
                    
                    # Handle rate limiting
                    if response.status_code == 429:  # Too Many Requests
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                        raise RateLimitExceededError(
                            status_code=response.status_code,
                            retry_after=retry_after,
                            details=response.json() if response.content else {}
                        )
                    
                    # Try to extract error details from the response
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', error_msg)
                        details = error_data
                    except ValueError:
                        details = {'raw_response': response.text}
                    
                    raise ApiClientError(
                        message=error_msg,
                        status_code=response.status_code,
                        details=details
                    )
                
                # Parse and validate the response
                try:
                    result = response.json()
                    
                    # If a model was provided, validate the response
                    if model is not None:
                        if isinstance(result, list):
                            return [model(**item) for item in result]
                        return model(**result)
                    
                    return result
                    
                except ValueError as e:
                    raise ApiClientError(
                        message=f"Failed to parse JSON response: {str(e)}",
                        status_code=response.status_code,
                        details={'raw_response': response.text}
                    )
                
            except (httpx.RequestError, ApiClientError) as e:
                last_error = e
                
                # If we've reached max retries, give up
                if retry_count >= self.max_retries:
                    break
                
                # Exponential backoff
                delay = self.retry_delay * (2 ** retry_count)
                logger.warning(f"Request failed (attempt {retry_count + 1}/{self.max_retries + 1}): {str(e)}. Retrying in {delay:.1f}s...")
                
                # Special handling for rate limiting
                if isinstance(e, RateLimitExceededError) and e.retry_after:
                    delay = e.retry_after
                
                await asyncio.sleep(delay)
                retry_count += 1
        
        # If we get here, all retries have failed
        if use_mock_fallback:
            logger.warning(f"All retries failed, falling back to mock data. Last error: {str(last_error)}")
            return await self._get_mock_data(method, endpoint, params, data)
        
        # Re-raise the last error
        raise last_error or ApiClientError("Unknown error occurred")
    
    @abstractmethod
    async def _get_mock_data(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get mock data for the given request.
        
        This method should be implemented by subclasses to provide mock data
        when the real API is unavailable.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            
        Returns:
            Mock response data
        """
        raise NotImplementedError("Subclasses must implement _get_mock_data")
