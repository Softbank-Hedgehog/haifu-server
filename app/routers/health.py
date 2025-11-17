from fastapi import APIRouter
from app.schemas.common import success_response, ApiResponse, HealthStatus, common_responses

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=ApiResponse[HealthStatus], responses=common_responses)
def health():
    return success_response(
        data={"status": "ok"},
        message="Server is healthy"
    )