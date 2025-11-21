# app/routers/projects.py
from fastapi import APIRouter, Depends
from typing import List

from app.core.security import get_current_user
from app.schemas.common import success_response, ApiResponse, common_responses
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.service.project_service import ProjectService


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ApiResponse[ProjectResponse], responses=common_responses, status_code=201)
async def create_project(
    data: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    프로젝트 생성

    Args:
        data: 프로젝트 생성 데이터
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        생성된 프로젝트 정보
    """
    user_id = current_user['user_id']
    project = await ProjectService.create_project(user_id, data)

    return success_response(
        data=project.model_dump(),
        message="Project created successfully"
    )


@router.get("", response_model=ApiResponse[List[ProjectResponse]], responses=common_responses)
async def list_projects(
    current_user: dict = Depends(get_current_user)
):
    """
    프로젝트 목록 조회

    Args:
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        사용자의 프로젝트 목록 (최신순)
    """
    user_id = current_user['user_id']
    projects = await ProjectService.list_projects(user_id)

    return success_response(
        data=[p.model_dump() for p in projects],
        message="Projects retrieved successfully"
    )


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse], responses=common_responses)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    프로젝트 상세 조회

    Args:
        project_id: 프로젝트 ID
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        프로젝트 상세 정보
    """
    user_id = current_user['user_id']
    project = await ProjectService.get_project(user_id, project_id)

    return success_response(
        data=project.model_dump(),
        message="Project retrieved successfully"
    )


@router.put("/{project_id}", response_model=ApiResponse[ProjectResponse], responses=common_responses)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    프로젝트 수정

    Args:
        project_id: 프로젝트 ID
        data: 수정할 데이터
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        수정된 프로젝트 정보
    """
    user_id = current_user['user_id']
    project = await ProjectService.update_project(user_id, project_id, data)

    return success_response(
        data=project.model_dump(),
        message="Project updated successfully"
    )


@router.delete("/{project_id}", response_model=ApiResponse[None], responses=common_responses)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    프로젝트 삭제 (하위 서비스도 모두 삭제)

    Args:
        project_id: 프로젝트 ID
        current_user: JWT 토큰에서 추출한 사용자 정보

    Returns:
        삭제 성공 메시지
    """
    user_id = current_user['user_id']
    await ProjectService.delete_project(user_id, project_id)

    return success_response(
        data=None,
        message="Project deleted successfully"
    )
