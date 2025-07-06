from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.groq_service import groq_service, GroqServiceError
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()

class InsightRequest(BaseModel):
    """Request model for getting insights"""
    flight_data: Dict[str, Any] = Field(..., description="Flight data to analyze")
    model: str = Field("mixtral-8x7b-32768", description="Groq model to use")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Controls randomness")
    max_tokens: int = Field(2000, gt=0, description="Maximum tokens to generate")

@router.post("/insights", response_model=Dict[str, Any])
async def get_insights(
    request: InsightRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AI-powered insights from flight data using Groq
    
    This endpoint analyzes flight booking data and provides insights about
    demand patterns, pricing trends, and travel recommendations.
    
    - **flight_data**: Flight data to analyze (must include booking information)
    - **model**: Groq model to use (default: mixtral-8x7b-32768)
    - **temperature**: Controls randomness (0.0 to 1.0)
    - **max_tokens**: Maximum number of tokens to generate
    
    Returns:
        JSON with insights and analysis
    """
    try:
        insights = await groq_service.get_insights(
            data=request.flight_data,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return {
            "status": "success",
            "data": insights,
            "model": request.model
        }
    except GroqServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(e),
                "suggestion": "Please check your API key and try again with valid data."
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "An unexpected error occurred",
                "error": str(e)
            }
        )

# Add endpoint for getting available models
@router.get("/models", response_model=Dict[str, Any])
async def get_available_models(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available Groq models
    
    Returns a list of available models that can be used for generating insights.
    """
    try:
        return {
            "status": "success",
            "models": [
                {
                    "id": "mixtral-8x7b-32768",
                    "name": "Mixtral 8x7B",
                    "description": "High-quality text generation with 32K context length",
                    "max_tokens": 32768
                },
                {
                    "id": "llama2-70b-4096",
                    "name": "LLaMA 2 70B",
                    "description": "Powerful 70B parameter model with 4K context",
                    "max_tokens": 4096
                },
                {
                    "id": "gemma-7b-it",
                    "name": "Gemma 7B",
                    "description": "Efficient 7B parameter model for instruction following",
                    "max_tokens": 8192
                }
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to fetch available models",
                "error": str(e)
            }
        )
