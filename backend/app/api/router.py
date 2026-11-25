from fastapi import APIRouter

from .routes import analytics, blockchain, dashboard, health, predictions, settings, transactions

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(transactions.router)
api_router.include_router(predictions.router)
api_router.include_router(analytics.router)
api_router.include_router(settings.router)
api_router.include_router(blockchain.router)
