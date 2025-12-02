"""Routers package"""

from .games import router as games_router
from .chat import router as chat_router

__all__ = ["games_router", "chat_router"]
