"""
Tests for Groq API integration.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.services.groq_service import GroqService, GroqServiceError

client = TestClient(app)

# Sample flight data for testing
SAMPLE_FLIGHT_DATA = {
    "data": [
        {
            "id": "1",
            "origin": {"iataCode": "SYD", "name": "Sydney"},
            "destination": {"iataCode": "MEL", "name": "Melbourne"},
            "departure": "2023-06-01T08:00:00",
            "arrival": "2023-06-01T09:30:00",
            "price": {"total": "150.00", "currency": "AUD"},
            "airline": {"code": "QF", "name": "Qantas"}
        },
        {
            "id": "2",
            "origin": {"iataCode": "MEL", "name": "Melbourne"},
            "destination": {"iataCode": "SYD", "name": "Sydney"},
            "departure": "2023-06-02T10:00:00",
            "arrival": "2023-06-02T11:30:00",
            "price": {"total": "120.00", "currency": "AUD"},
            "airline": {"code": "VA", "name": "Virgin Australia"}
        }
    ],
    "meta": {
        "count": 2,
        "start_date": "2023-06-01",
        "end_date": "2023-06-02"
    }
}

@pytest.fixture
def mock_groq_response():
    """Mock successful Groq API response."""
    return {
        "id": "test-123",
        "object": "chat.completion",
        "created": 1620000000,
        "model": "mixtral-8x7b-32768",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": """{
                        "summary": "Analysis of flight data",
                        "demand_analysis": "High demand observed on SYD-MEL route",
                        "pricing_analysis": "Average price is $135.00 AUD",
                        "recommendations": ["Consider adding more flights on this route"],
                        "key_metrics": {"total_flights": 2, "avg_price": 135.0}
                    }"""
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300
        }
    }

@patch('app.services.groq_service.httpx.AsyncClient.post')
@pytest.mark.asyncio
async def test_get_insights_success(mock_post, mock_groq_response):
    """Test successful retrieval of insights from Groq API."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_groq_response
    mock_post.return_value.__aenter__.return_value = mock_response
    
    # Initialize service
    service = GroqService(api_key="test-api-key")
    
    # Call the method
    result = await service.get_insights(SAMPLE_FLIGHT_DATA)
    
    # Assertions
    assert "summary" in result
    assert "demand_analysis" in result
    assert "pricing_analysis" in result
    assert "recommendations" in result
    assert "key_metrics" in result
    
    # Verify the API was called with correct parameters
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "chat/completions" in args[0]
    assert kwargs["headers"]["Authorization"] == "Bearer test-api-key"

@patch('app.services.groq_service.httpx.AsyncClient.post')
@pytest.mark.asyncio
async def test_get_insights_rate_limit(mock_post):
    """Test handling of rate limiting from Groq API."""
    # Setup mock to simulate rate limit
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_post.return_value.__aenter__.return_value = mock_response
    
    # Initialize service
    service = GroqService(api_key="test-api-key")
    
    # Call the method and expect an exception
    with pytest.raises(GroqServiceError, match="Rate limit exceeded"):
        await service.get_insights(SAMPLE_FLIGHT_DATA)

@patch('app.services.groq_service.httpx.AsyncClient.post')
@pytest.mark.asyncio
async def test_get_insights_invalid_json(mock_post):
    """Test handling of invalid JSON response from Groq API."""
    # Setup mock to return non-JSON response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is not valid JSON"}}]
    }
    mock_post.return_value.__aenter__.return_value = mock_response
    
    # Initialize service
    service = GroqService(api_key="test-api-key")
    
    # Call the method - should handle invalid JSON gracefully
    result = await service.get_insights(SAMPLE_FLIGHT_DATA)
    assert isinstance(result, dict)
    assert "insights" in result

@patch.dict(os.environ, {"GROQ_API_KEY": "test-env-key"}, clear=True)
def test_groq_service_initialization():
    """Test GroqService initialization with environment variable."""
    service = GroqService()
    assert service.api_key == "test-env-key"

def test_groq_service_without_api_key():
    """Test GroqService initialization without API key."""
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=True):
        service = GroqService()
        assert service.api_key is None

@pytest.mark.integration
@patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=True)
def test_insights_endpoint_requires_auth():
    """Test that insights endpoint requires authentication."""
    response = client.post(
        "/api/v1/insights/insights",
        json={"flight_data": SAMPLE_FLIGHT_DATA}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@patch('app.services.groq_service.GroqService.get_insights')
def test_insights_endpoint_success(mock_get_insights, test_user, client):
    """Test successful request to insights endpoint."""
    # Setup mock
    mock_insights = {
        "summary": "Test insights",
        "demand_analysis": "Test demand",
        "pricing_analysis": "Test pricing",
        "recommendations": ["Test recommendation"],
        "key_metrics": {"test": "metric"}
    }
    mock_get_insights.return_value = mock_insights
    
    # Get auth token
    token_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"}
    )
    token = token_response.json()["access_token"]
    
    # Make request
    response = client.post(
        "/api/v1/insights/insights",
        json={"flight_data": SAMPLE_FLIGHT_DATA},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "success"
    assert response.json()["data"] == mock_insights
