from typing import Dict, Any, Optional, List
import os
import json
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel, Field
from enum import Enum

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class GroqModel(str, Enum):
    MIXTRAL_8X7B = "mixtral-8x7b-32768"
    LLAMA2_70B = "llama2-70b-4096"
    GEMMA_7B = "gemma-7b-it"

class GroqServiceError(Exception):
    """Custom exception for Groq service errors"""
    pass

class GroqService:
    """Service for interacting with Groq's API for travel insights"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = 30.0
        self.max_retries = 3
    
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the Groq API with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        url,
                        headers=self.headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limit
                        if attempt == self.max_retries - 1:
                            raise GroqServiceError("Rate limit exceeded. Please try again later.")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise GroqServiceError(f"API request failed: {str(e)}")
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise GroqServiceError(f"Request failed after {self.max_retries} attempts: {str(e)}")
                    await asyncio.sleep(1)  # Simple backoff
    
    async def get_insights(
        self,
        data: Dict[str, Any],
        model: GroqModel = GroqModel.MIXTRAL_8X7B,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Get AI-powered insights from flight data
        
        Args:
            data: Flight data to analyze
            model: Groq model to use
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary containing insights
        """
        try:
            # Prepare the prompt
            prompt = self._build_insights_prompt(data)
            
            # Prepare the request payload
            payload = {
                "model": model.value,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a travel industry analyst. Provide clear, data-driven insights 
                        about flight booking trends, pricing patterns, and travel demand. Focus on actionable 
                        insights for travel businesses."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Make the API request
            response = await self._make_request("chat/completions", payload)
            
            # Parse and return the response
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                try:
                    # Try to parse as JSON if the response is JSON-formatted
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    return {"insights": content}
            
            return {"error": "No insights generated"}
            
        except Exception as e:
            logger.error(f"Error getting insights from Groq: {str(e)}")
            raise GroqServiceError(f"Failed to get insights: {str(e)}")
    
    def _build_insights_prompt(self, data: Dict[str, Any]) -> str:
        """Build a prompt for flight data analysis"""
        return f"""Analyze the following flight booking data and provide insights:
        
        Flight Data Summary:
        - Total bookings: {data.get('meta', {}).get('count', 0)}
        - Time period: {data.get('meta', {}).get('start_date', 'N/A')} to {data.get('meta', {}).get('end_date', 'N/A')}
        - Routes: {', '.join(set(f"{f.get('origin', {}).get('iataCode', '?')}-{f.get('destination', {}).get('iataCode', '?')}" for f in data.get('data', [])))}
        
        Please provide insights on:
        1. Demand patterns and trends
        2. Price movements and anomalies
        3. Busiest routes and times
        4. Any notable patterns or recommendations
        5. Potential opportunities or risks
        
        Format your response as a JSON object with these sections:
        - summary: Brief overview
        - demand_analysis: Detailed demand insights
        - pricing_analysis: Price trends and observations
        - recommendations: Actionable recommendations
        - key_metrics: Important statistics
        """

# Singleton instance
groq_service = GroqService()

# Example usage:
"""
async def example():
    flight_data = {
        "data": [...],  # Your flight data
        "meta": {
            "count": 100,
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
    }
    
    try:
        insights = await groq_service.get_insights(flight_data)
        print(insights)
    except GroqServiceError as e:
        print(f"Error: {e}")
"""
