from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.restaurants import router as restaurants_router
from app.api.menu import router as menu_router
from app.api.orders import router as orders_router
from app.api.order_items import router as order_items_router
from app.api.stations import router as stations_router
from app.api.metrics import router as metrics_router
from app.api.ai import router as ai_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(restaurants_router)
api_router.include_router(menu_router)
api_router.include_router(orders_router)
api_router.include_router(order_items_router)
api_router.include_router(stations_router)
api_router.include_router(metrics_router)
api_router.include_router(ai_router)
