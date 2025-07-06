"""
API endpoints package.

This module exposes the API endpoint routers for the application.
"""
from fastapi import APIRouter

# Import all endpoint modules here
from . import auth, flights

# Create a router for endpoints
router = APIRouter()

# Include the auth router
router.include_router(auth.router)

# Include the flights router
router.include_router(flights.router)
