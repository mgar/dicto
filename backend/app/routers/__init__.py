"""
API Routers package.
"""
from .auth import router as auth_router
from .grammar import router as grammar_router
from .learn import router as learn_router
from .reviews import router as reviews_router
from .stats import router as stats_router
from .vocab import router as vocab_router

__all__ = [
    "auth_router",
    "grammar_router",
    "learn_router",
    "reviews_router",
    "stats_router",
    "vocab_router",
]
