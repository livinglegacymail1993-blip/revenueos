from fastapi import APIRouter

from .analyze import analyze_router
from .connect import connect_router

router = APIRouter()
# Placeholder for additional routes

__all__ = ["router", "analyze_router", "connect_router"]