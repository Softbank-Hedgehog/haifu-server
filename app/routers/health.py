from fastapi import APIRouter
from app.schemas.common import success_response, ApiResponse, HealthStatus, common_responses

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=ApiResponse[HealthStatus], responses=common_responses)
def health():
    return success_response(
        data={"status": "ok"},
        message="Server is healthy"
    )

@router.get("/healthz", response_model=ApiResponse[HealthStatus], responses=common_responses)
def healthz():
    """Kubernetes/ECS style health check"""
    return success_response(
        data={"status": "ok"},
        message="Server is healthy"
    )