from fastapi import APIRouter
from app.api.v1.routes.routes import router as test_router
from app.api.v1.routes.water_sample import router as water_sample_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.measurement import router as measurement_router

api_router = APIRouter()
api_router.include_router(test_router, tags=["health"])
api_router.include_router(water_sample_router, tags=["water sample"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(measurement_router, tags=["measurement"])
