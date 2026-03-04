from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="API health check")
def health_check():
    return {"status": "ok", "service": "falilaX-api", "version": "v1"}