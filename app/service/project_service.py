# app/service/project_service.py
from datetime import datetime
from typing import List, Optional
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException

from app.database import projects_table, services_table, get_item, put_item, update_item, delete_item, query_items
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse


class ProjectService:
    """프로젝트 관련 비즈니스 로직"""

    @staticmethod
    async def create_project(user_id: int, data: ProjectCreate) -> ProjectResponse:
        """
        프로젝트 생성

        Args:
            user_id: 사용자 GitHub user ID
            data: 프로젝트 생성 데이터

        Returns:
            생성된 프로젝트 정보

        Raises:
            HTTPException: 생성 실패 시
        """
        now = datetime.utcnow().isoformat() + 'Z'

        item = {
            'user_id': user_id,
            'project_id': data.id,
            'name': data.name,
            'description': data.description,
            'created_at': now,
            'updated_at': now
        }

        try:
            await put_item(projects_table, item)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

        # ProjectResponse는 'id' 필드를 요구하므로 'project_id'를 'id'로 매핑
        response_data = {
            'id': item['project_id'],
            'name': item['name'],
            'description': item['description'],
            'user_id': item['user_id'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at']
        }
        return ProjectResponse(**response_data)

    @staticmethod
    async def get_project(user_id: int, project_id: str) -> ProjectResponse:
        """
        프로젝트 조회

        Args:
            user_id: 사용자 GitHub user ID
            project_id: 프로젝트 ID

        Returns:
            프로젝트 정보

        Raises:
            HTTPException: 프로젝트가 없거나 권한이 없는 경우
        """
        try:
            item = await get_item(
                projects_table,
                key={'user_id': user_id, 'project_id': project_id}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")

        if not item:
            raise HTTPException(status_code=404, detail="Project not found")

        # ProjectResponse는 'id' 필드를 요구하므로 'project_id'를 'id'로 매핑
        response_data = {
            'id': item['project_id'],
            'name': item['name'],
            'description': item.get('description'),
            'user_id': item['user_id'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at']
        }
        return ProjectResponse(**response_data)

    @staticmethod
    async def list_projects(user_id: int) -> List[ProjectResponse]:
        """
        사용자의 프로젝트 목록 조회

        Args:
            user_id: 사용자 GitHub user ID

        Returns:
            프로젝트 목록 (최신순)
        """
        try:
            items = await query_items(
                projects_table,
                key_condition_expression=Key('user_id').eq(user_id),
                ScanIndexForward=False  # 내림차순 정렬
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

        # updated_at 기준 정렬 (최신순)
        items.sort(key=lambda x: x.get('updated_at', ''), reverse=True)

        # ProjectResponse는 'id' 필드를 요구하므로 'project_id'를 'id'로 매핑
        return [ProjectResponse(
            id=item['project_id'],
            name=item['name'],
            description=item.get('description'),
            user_id=item['user_id'],
            created_at=item['created_at'],
            updated_at=item['updated_at']
        ) for item in items]

    @staticmethod
    async def update_project(user_id: int, project_id: str, data: ProjectUpdate) -> ProjectResponse:
        """
        프로젝트 수정

        Args:
            user_id: 사용자 GitHub user ID
            project_id: 프로젝트 ID
            data: 수정할 데이터

        Returns:
            수정된 프로젝트 정보

        Raises:
            HTTPException: 프로젝트가 없거나 권한이 없는 경우
        """
        # 프로젝트 존재 확인 및 권한 체크
        await ProjectService.get_project(user_id, project_id)

        # 수정할 필드만 추출 (None이 아닌 값만)
        updates = {}
        if data.name is not None:
            updates['name'] = data.name
        if data.description is not None:
            updates['description'] = data.description

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # updated_at 갱신
        updates['updated_at'] = datetime.utcnow().isoformat() + 'Z'

        try:
            updated_item = await update_item(
                projects_table,
                key={'user_id': user_id, 'project_id': project_id},
                updates=updates
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

        # ProjectResponse는 'id' 필드를 요구하므로 'project_id'를 'id'로 매핑
        response_data = {
            'id': updated_item['project_id'],
            'name': updated_item['name'],
            'description': updated_item.get('description'),
            'user_id': updated_item['user_id'],
            'created_at': updated_item['created_at'],
            'updated_at': updated_item['updated_at']
        }
        return ProjectResponse(**response_data)

    @staticmethod
    async def delete_project(user_id: int, project_id: str) -> bool:
        """
        프로젝트 삭제 (하위 서비스도 모두 삭제)

        Args:
            user_id: 사용자 GitHub user ID
            project_id: 프로젝트 ID

        Returns:
            삭제 성공 여부

        Raises:
            HTTPException: 프로젝트가 없거나 권한이 없는 경우
        """
        # 프로젝트 존재 확인 및 권한 체크
        await ProjectService.get_project(user_id, project_id)

        try:
            # 1. 하위 서비스 모두 삭제
            services = await query_items(
                services_table,
                key_condition_expression=Key('project_id').eq(project_id)
            )

            for service in services:
                # 권한 확인 (user_id 일치 여부)
                if service.get('user_id') != user_id:
                    raise HTTPException(status_code=403, detail="Forbidden: Cannot delete service")

                await delete_item(
                    services_table,
                    key={'project_id': project_id, 'service_id': service['service_id']}
                )

            # 2. 프로젝트 삭제
            await delete_item(
                projects_table,
                key={'user_id': user_id, 'project_id': project_id}
            )

            return True

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
