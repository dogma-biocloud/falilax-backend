from fastapi import APIRouter
from app.schemas.map import MapNetworkResponse
from app.services.map_service import build_demo_map_network

router = APIRouter(prefix="/map", tags=["Map"])


@router.get("/network", response_model=MapNetworkResponse)
def get_map_network() -> MapNetworkResponse:
    return build_demo_map_network()