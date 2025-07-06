"""
API v1 package.
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import flights, market, airports
from app.api.endpoints import insights as insights_endpoint

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(flights.router, prefix="/flights", tags=["flights"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(airports.router, prefix="/airports", tags=["airports"])
api_router.include_router(insights_endpoint.router, prefix="/insights", tags=["insights"])
