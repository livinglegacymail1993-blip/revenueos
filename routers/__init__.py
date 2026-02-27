from fastapi import APIRouter

from .analyze import analyze_router

router = APIRouter()
# Placeholder for additional routes

__all__ = ["router", "analyze_router"]