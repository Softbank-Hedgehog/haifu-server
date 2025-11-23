from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas.common import common_responses, ApiResponse, success_response
from app.schemas.service import DeployResponse
from app.service.service_service import ServiceService

router = APIRouter(prefix="/deploy")

@router.post(
    "/{service_id}",
    response_model=ApiResponse[DeployResponse],
    responses=common_responses,
    status_code=202,  # 비동기 배포 트리거니까 202 추천
)
async def deploy_service(
    service_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    서비스 배포 트리거

    Path:
        service_id: 배포할 서비스 ID

    Auth:
        JWT에서 user_id 추출

    Returns:
        배포 요청 결과 (queued 상태)
    """
    user_id = str(current_user["user_id"])

    result = await ServiceService.deploy_service(user_id, service_id)

    return success_response(
        data=result.model_dump(),
        message="Deployment triggered successfully",
    )
