# API Documentation

This document provides detailed information about the Airline Market Demand API endpoints, request/response formats, and authentication requirements.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require authentication. Include the JWT token in the `Authorization` header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Authentication

#### Register a new user
```http
POST /auth/register
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

#### Login
```http
POST /auth/login
```

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Flights

#### Search Flights
```http
GET /flights/search
```

**Query Parameters**:
- `origin`: IATA airport code (e.g., "SYD")
- `destination`: IATA airport code (e.g., "MEL")
- `departure_date`: Date in YYYY-MM-DD format
- `return_date`: Optional, Date in YYYY-MM-DD format
- `adults`: Number of adult passengers (default: 1)
- `cabin_class`: Economy, Premium Economy, Business, First (default: Economy)

**Response**:
```json
{
  "data": [
    {
      "id": "flt_123",
      "airline": "QF",
      "flight_number": "QF400",
      "origin": "SYD",
      "destination": "MEL",
      "departure_time": "2023-12-01T08:00:00",
      "arrival_time": "2023-12-01T09:30:00",
      "price": 199.99,
      "currency": "AUD",
      "available_seats": 42,
      "cabin_class": "Economy"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 10
  }
}
```

### Airports

#### List Airports
```http
GET /airports
```

**Query Parameters**:
- `search`: Optional search term for airport name or IATA code
- `country`: Optional filter by country code (e.g., "AU")
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10, max: 100)

**Response**:
```json
{
  "data": [
    {
      "iata_code": "SYD",
      "name": "Sydney Airport",
      "city": "Sydney",
      "country": "Australia",
      "timezone": "Australia/Sydney",
      "latitude": -33.946111,
      "longitude": 151.177222
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 10
  }
}
```

### Market Data

#### Get Market Trends
```http
GET /market/trends
```

**Query Parameters**:
- `origin`: IATA airport code (required)
- `destination`: IATA airport code (required)
- `start_date`: Start date in YYYY-MM-DD format (default: today)
- `end_date`: End date in YYYY-MM-DD format (default: today + 30 days)
- `metrics`: Comma-separated list of metrics (e.g., "price,demand,capacity")

**Response**:
```json
{
  "origin": "SYD",
  "destination": "MEL",
  "period": {
    "start_date": "2023-12-01",
    "end_date": "2023-12-31"
  },
  "data": [
    {
      "date": "2023-12-01",
      "average_price": 199.99,
      "min_price": 149.99,
      "max_price": 349.99,
      "demand_level": 0.85,
      "available_seats": 1200,
      "total_seats": 1500
    }
  ]
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["string", 0],
      "msg": "string",
      "type": "string"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- 100 requests per minute per IP address for unauthenticated users
- 1000 requests per minute per user for authenticated users

## WebSocket Endpoints

### Real-time Flight Updates
```
ws://localhost:8000/ws/flights/{flight_id}
```

**Example Payload**:
```json
{
  "event": "status_update",
  "data": {
    "flight_id": "flt_123",
    "status": "on_time",
    "updated_at": "2023-12-01T08:05:00Z"
  }
}
```

## Webhooks

### Flight Price Alert
```
POST /webhooks/price-alert
```

**Headers**:
- `X-Webhook-Signature`: HMAC-SHA256 signature of the payload

**Payload**:
```json
{
  "alert_id": "alert_123",
  "flight_id": "flt_123",
  "original_price": 199.99,
  "current_price": 149.99,
  "price_drop_percent": 25,
  "triggered_at": "2023-12-01T08:00:00Z"
}
```
