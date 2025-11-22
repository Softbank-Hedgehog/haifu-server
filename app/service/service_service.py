# app/service/service_service.py
from datetime import datetime
from typing import List
from boto3.dynamodb.conditions import Key
from fastapi import HTTPException

from app.database import (
    services_table,
    get_item,
    put_item,
    update_item,
    delete_item,
    query_items,
)
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.service.project_service import ProjectService


class ServiceService:
    """서비스(배포) 관련 비즈니스 로직"""

    @staticmethod
    async def create_service(user_id: str, project_id: str, data: ServiceCreate) -> ServiceResponse:
        """
        서비스 생성
        """
        # 1. 프로젝트 존재 확인 및 권한 체크
        await ProjectService.get_project(user_id, project_id)

        # 2. CPU-Memory 조합 검증
        try:
            data.validate_cpu_memory_combination()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # 3. 서비스 생성
        now = datetime.utcnow().isoformat() + "Z"

        item = {
            "project_id": project_id,
            "service_id": data.id,
            "user_id": user_id,  # 권한 체크용 / 필요시 GSI 용도
            "name": data.name,
            "repo_owner": data.repo_owner,
            "repo_name": data.repo_name,
            "branch": data.branch,
            "runtime": data.runtime,
            "cpu": data.cpu,
            "memory": data.memory,
            "port": data.port,
            "build_command": data.build_command,
            "start_command": data.start_command,
            "environment_variables": data.environment_variables or {},
            "status": "pending",  # 초기 상태
            "deployment_url": None,
            "created_at": now,
            "updated_at": now,
        }

        try:
            await put_item(services_table, item)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create service: {str(e)}")

        response_data = {
            "id": item["service_id"],
            "project_id": item["project_id"],
            "name": item["name"],
            "repo_owner": item["repo_owner"],
            "repo_name": item["repo_name"],
            "branch": item["branch"],
            "runtime": item["runtime"],
            "cpu": item["cpu"],
            "memory": item["memory"],
            "port": item["port"],
            "build_command": item.get("build_command"),
            "start_command": item.get("start_command"),
            "environment_variables": item.get("environment_variables"),
            "status": item["status"],
            "deployment_url": item.get("deployment_url"),
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }
        return ServiceResponse(**response_data)

    @staticmethod
    async def get_service(user_id: str, service_id: str, project_id: str) -> ServiceResponse:
        """
        서비스 조회
        """
        try:
            # 테이블 기본 키(service_id)로 조회
            item = await get_item(
                services_table,
                key={"service_id": service_id},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")

        # 아이템이 없거나 project_id가 다르면 404
        if not item or item.get("project_id") != project_id:
            raise HTTPException(status_code=404, detail="Service not found")

        # 권한 확인
        if item.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Forbidden: Access denied")

        response_data = {
            "id": item["service_id"],
            "project_id": item["project_id"],
            "name": item["name"],
            "repo_owner": item["repo_owner"],
            "repo_name": item["repo_name"],
            "branch": item["branch"],
            "runtime": item["runtime"],
            "cpu": item["cpu"],
            "memory": item["memory"],
            "port": item["port"],
            "build_command": item.get("build_command"),
            "start_command": item.get("start_command"),
            "environment_variables": item.get("environment_variables"),
            "status": item["status"],
            "deployment_url": item.get("deployment_url"),
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }
        return ServiceResponse(**response_data)

    @staticmethod
    async def list_services(user_id: str, project_id: str) -> List[ServiceResponse]:
        """
        프로젝트 내 서비스 목록 조회
        """
        # 프로젝트 존재 확인 및 권한 체크
        await ProjectService.get_project(user_id, project_id)

        try:
            # GSI(project-index, PK = project_id) 사용
            items = await query_items(
                services_table,
                key_condition_expression=Key("project_id").eq(project_id),
                index_name="project-index",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")

        # updated_at 기준 정렬 (최신순)
        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return [
            ServiceResponse(
                id=item["service_id"],
                project_id=item["project_id"],
                name=item["name"],
                repo_owner=item["repo_owner"],
                repo_name=item["repo_name"],
                branch=item["branch"],
                runtime=item["runtime"],
                cpu=item["cpu"],
                memory=item["memory"],
                port=item["port"],
                build_command=item.get("build_command"),
                start_command=item.get("start_command"),
                environment_variables=item.get("environment_variables"),
                status=item["status"],
                deployment_url=item.get("deployment_url"),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
            for item in items
        ]

    @staticmethod
    async def update_service(
        user_id: str,
        service_id: str,
        project_id: str,
        data: ServiceUpdate,
    ) -> ServiceResponse:
        """
        서비스 수정
        """
        # 서비스 존재 확인 및 권한 체크
        existing_service = await ServiceService.get_service(user_id, service_id, project_id)

        # 수정할 필드만 추출 (None이 아닌 값만)
        updates = {}
        if data.name is not None:
            updates["name"] = data.name
        if data.branch is not None:
            updates["branch"] = data.branch
        if data.runtime is not None:
            updates["runtime"] = data.runtime
        if data.cpu is not None:
            updates["cpu"] = data.cpu
        if data.memory is not None:
            updates["memory"] = data.memory
        if data.port is not None:
            updates["port"] = data.port
        if data.build_command is not None:
            updates["build_command"] = data.build_command
        if data.start_command is not None:
            updates["start_command"] = data.start_command
        if data.environment_variables is not None:
            updates["environment_variables"] = data.environment_variables

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # CPU-Memory 조합 검증 (둘 다 수정되는 경우)
        if "cpu" in updates or "memory" in updates:
            from app.schemas.service import CPU_MEMORY_COMBINATIONS

            final_cpu = updates.get("cpu", existing_service.cpu)
            final_memory = updates.get("memory", existing_service.memory)

            allowed_memory = CPU_MEMORY_COMBINATIONS.get(final_cpu, [])
            if final_memory not in allowed_memory:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid CPU-Memory combination. {final_cpu} supports: {', '.join(allowed_memory)}",
                )

        # updated_at 갱신
        updates["updated_at"] = datetime.utcnow().isoformat() + "Z"

        try:
            updated_item = await update_item(
                services_table,
                key={"service_id": service_id},  # 테이블 PK만 사용
                updates=updates,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update service: {str(e)}")

        response_data = {
            "id": updated_item["service_id"],
            "project_id": updated_item["project_id"],
            "name": updated_item["name"],
            "repo_owner": updated_item["repo_owner"],
            "repo_name": updated_item["repo_name"],
            "branch": updated_item["branch"],
            "runtime": updated_item["runtime"],
            "cpu": updated_item["cpu"],
            "memory": updated_item["memory"],
            "port": updated_item["port"],
            "build_command": updated_item.get("build_command"),
            "start_command": updated_item.get("start_command"),
            "environment_variables": updated_item.get("environment_variables"),
            "status": updated_item["status"],
            "deployment_url": updated_item.get("deployment_url"),
            "created_at": updated_item["created_at"],
            "updated_at": updated_item["updated_at"],
        }
        return ServiceResponse(**response_data)

    @staticmethod
    async def delete_service(user_id: str, service_id: str, project_id: str) -> bool:
        """
        서비스 삭제
        """
        # 서비스 존재 확인 및 권한 체크
        await ServiceService.get_service(user_id, service_id, project_id)

        try:
            await delete_item(
                services_table,
                key={"service_id": service_id},  # 테이블 PK만 사용
            )
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete service: {str(e)}")
