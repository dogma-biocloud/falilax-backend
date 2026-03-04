from fastapi import APIRouter

from app.api.v1.routes import health
from app.api.v1.routes import water_sample
from app.api.v1.routes import routes  # this is your db-test router
from app.api.v1.routes import measurement  # we will create this next

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(water_sample.router)
api_router.include_router(routes.router)
api_router.include_router(measurement.router)