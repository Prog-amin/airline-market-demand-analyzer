"""
API package initialization.

This module initializes the API package and sets up the main API router.
"""
from fastapi import APIRouter

# Import all endpoint modules here
from app.api.endpoints import auth, flights

# Create the main API router
api_router = APIRouter()

# Include the auth router
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Include the flights router
api_router.include_router(
    flights.router,
    prefix="/flights",
    tags=["Flights"]
)

# You can add more routers here as your application grows
# api_router.include_router(
#     some_other_router,
#     prefix="/some-prefix",
#     tags=["Some Tag"]
# )
