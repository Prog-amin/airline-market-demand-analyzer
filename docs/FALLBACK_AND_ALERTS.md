# Fallback Logic and User Alerts

This document outlines the fallback mechanisms and user alerting system implemented in the Airline Market Demand application to handle API failures gracefully.

## Fallback Strategy

The application implements a multi-layered fallback strategy to ensure data availability even when external APIs are unavailable:

1. **Primary Data Source**: Real-time data from external APIs (Amadeus, AviationStack, etc.)
2. **Secondary Data Source**: Cached data from the database (if available)
3. **Tertiary Data Source**: Mock data generator (built-in fallback)

## Implementation Details

### 1. Data Service Layer

The `DataService` class handles all data retrieval with built-in fallback logic:

```python
class DataService:
    def __init__(self):
        self.providers = [
            AmadeusProvider(),
            AviationStackProvider(),
            RapidAPIProvider()
        ]
        self.cache = RedisCache()
        self.mock_provider = MockDataProvider()

    async def get_flight_data(self, **params):
        # Try cache first
        cache_key = self._generate_cache_key('flights', params)
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data

        # Try providers in order
        for provider in self.providers:
            try:
                data = await provider.get_flight_data(**params)
                if data:
                    # Cache successful response
                    await self.cache.set(cache_key, data, ttl=3600)
                    return data
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {str(e)}"
                continue

        # Fall back to mock data
        logger.warning("All providers failed, falling back to mock data")
        return await self.mock_provider.get_flight_data(**params)
```

### 2. Error Handling Middleware

Custom middleware captures and processes API failures:

```python
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except ExternalAPIError as e:
        # Log the error and trigger alerts
        logger.error(f"API Error: {str(e)}")
        await alert_service.send_alert(
            f"API Failure: {e.provider}",
            f"Error: {str(e)}\nURL: {request.url}",
            severity="warning"
        )
        
        # Try fallback if available
        if hasattr(e, 'fallback_data'):
            return JSONResponse(
                content={
                    "data": e.fallback_data,
                    "warning": f"Using fallback data: {str(e)}"
                },
                status_code=206  # Partial Content
            )
            
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
```

## User Alerts

### Types of Alerts

1. **Toast Notifications**: For non-critical issues that don't interrupt the user flow
2. **Banner Alerts**: For important warnings that require user attention
3. **Modal Dialogs**: For critical errors that require user action
4. **Email Notifications**: For important system events (admin only)

### Alert Configuration

Alerts are configured in `app/core/config.py`:

```python
class AlertSettings(BaseSettings):
    ENABLE_EMAIL_ALERTS: bool = True
    EMAIL_ALERT_RECIPIENTS: List[str] = ["admin@example.com"]
    MIN_SEVERITY_FOR_EMAIL: str = "warning"  # debug, info, warning, error, critical
    SLACK_WEBHOOK_URL: Optional[HttpUrl] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "ALERT_"
```

### Alert Service

The `AlertService` handles all alerting functionality:

```python
class AlertService:
    def __init__(self):
        self.settings = AlertSettings()
        self.email_client = EmailClient()
        self.slack_client = SlackClient() if self.settings.SLACK_WEBHOOK_URL else None

    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        user: Optional[User] = None
    ) -> bool:
        """
        Send an alert through all configured channels.
        
        Args:
            title: Short description of the alert
            message: Detailed message
            severity: debug, info, warning, error, or critical
            user: Optional user to receive the alert
        """
        # Log all alerts
        logger.log(
            getattr(logging, severity.upper(), logging.INFO),
            f"[{severity.upper()}] {title}: {message}"
        )
        
        # Send email alerts for important events
        if (self._should_send_email(severity) and 
            self.settings.ENABLE_EMAIL_ALERTS):
            await self._send_email_alert(title, message, severity, user)
            
        # Send to Slack if configured
        if self.slack_client and self._should_send_slack(severity):
            await self._send_slack_alert(title, message, severity)
            
        return True
```

## Monitoring and Metrics

### Prometheus Metrics

The application exposes the following metrics:

- `api_requests_total`: Total number of API requests
- `api_errors_total`: Number of failed API requests by provider
- `fallback_activations_total`: Number of times fallback was triggered
- `alert_events_total`: Number of alerts triggered by severity

### Health Check Endpoint

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2023-12-01T12:00:00Z",
  "services": {
    "database": {
      "status": "ok",
      "latency_ms": 12.5
    },
    "cache": {
      "status": "ok",
      "latency_ms": 2.1
    },
    "external_apis": {
      "amadeus": "ok",
      "aviationstack": "ok",
      "rapidapi": "error: connection timeout"
    }
  }
}
```

## Best Practices

1. **Graceful Degradation**: Always provide a fallback when possible
2. **Transparency**: Inform users when fallback data is being used
3. **Monitoring**: Track all fallback activations and alert on patterns
4. **Retry Logic**: Implement exponential backoff for transient failures
5. **Circuit Breaker**: Temporarily disable failing services to prevent cascading failures

## Example: Implementing a New Data Provider

1. Create a new provider class:

```python
class NewDataProvider(DataProvider):
    name = "new_provider"
    
    async def get_flight_data(self, **params):
        try:
            # Implementation here
            return data
        except Exception as e:
            raise ExternalAPIError(
                provider=self.name,
                message=str(e),
                fallback_data=await self._get_fallback_data(params)
            )
```

2. Add it to the providers list in `DataService`
3. Update the documentation with the new provider's capabilities and limitations
