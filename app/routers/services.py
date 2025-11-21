# app/routers/services.py
from fastapi import APIRouter, Depends, Query
from typing import List

from app.core.security import get_current_user
from app.schemas.common import success_response, ApiResponse, common_responses
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.service.service_service import ServiceService


router = APIRouter(tags=["Services"])


@router.post(
    "/projects/{project_id}/services",
    response_model=ApiResponse[ServiceResponse],
    responses=common_responses,
    status_code=201
)
async def create_service(
    project_id: str,
    data: ServiceCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    서비스 생성

    Args:
        project_id: 프로젝트 ID
        data: 서비스 생성 데이터
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        생성된 서비스 정보
    """
    user_id = current_user['user_id']
    service = await ServiceService.create_service(user_id, project_id, data)

    return success_response(
        data=service.model_dump(),
        message="Service created successfully"
    )


@router.get(
    "/projects/{project_id}/services",
    response_model=ApiResponse[List[ServiceResponse]],
    responses=common_responses
)
async def list_services(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    프로젝트 내 서비스 목록 조회

    Args:
        project_id: 프로젝트 ID
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        서비스 목록
    """
    user_id = current_user['user_id']
    services = await ServiceService.list_services(user_id, project_id)

    return success_response(
        data=[s.model_dump() for s in services],
        message="Services retrieved successfully"
    )


@router.get(
    "/services/{service_id}",
    response_model=ApiResponse[ServiceResponse],
    responses=common_responses
)
async def get_service(
    service_id: str,
    project_id: str = Query(..., description="프로젝트 ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    서비스 상세 조회

    Args:
        service_id: 서비스 ID
        project_id: 프로젝트 ID (Query Parameter)
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        서비스 상세 정보
    """
    user_id = current_user['user_id']
    service = await ServiceService.get_service(user_id, service_id, project_id)

    return success_response(
        data=service.model_dump(),
        message="Service retrieved successfully"
    )


@router.put(
    "/services/{service_id}",
    response_model=ApiResponse[ServiceResponse],
    responses=common_responses
)
async def update_service(
    service_id: str,
    data: ServiceUpdate,
    project_id: str = Query(..., description="프로젝트 ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    서비스 수정

    Args:
        service_id: 서비스 ID
        data: 수정할 데이터
        project_id: 프로젝트 ID (Query Parameter)
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        수정된 서비스 정보
    """
    user_id = current_user['user_id']
    service = await ServiceService.update_service(user_id, service_id, project_id, data)

    return success_response(
        data=service.model_dump(),
        message="Service updated successfully"
    )


@router.delete(
    "/services/{service_id}",
    response_model=ApiResponse[None],
    responses=common_responses
)
async def delete_service(
    service_id: str,
    project_id: str = Query(..., description="프로젝트 ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    서비스 삭제

    Args:
        service_id: 서비스 ID
        project_id: 프로젝트 ID (Query Parameter)
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        삭제 성공 메시지
    """
    user_id = current_user['user_id']
    await ServiceService.delete_service(user_id, service_id, project_id)

    return success_response(
        data=None,
        message="Service deleted successfully"
    )
