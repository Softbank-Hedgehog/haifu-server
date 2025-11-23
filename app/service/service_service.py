# app/service/service_service.py
import json
import os
from datetime import datetime
from decimal import Decimal
from typing import List

import boto3
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
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse, DeployResponse
from app.service.project_service import ProjectService


lambda_client = boto3.client("lambda")
DEPLOY_LAMBDA_NAME = "haifu-dev-deployment"  # or ARN

class ServiceService:
    """서비스(배포) 관련 비즈니스 로직"""

    @staticmethod
    async def create_service(user_id: str, project_id: str, data: ServiceCreate) -> ServiceResponse:
        """
        서비스 생성
        """

        # 1. 프로젝트 존재 확인 및 권한 체크
        await ProjectService.get_project(user_id, project_id)

        now = datetime.utcnow().isoformat() + "Z"

        # 공통 필드 (static / dynamic 둘 다 공통으로 가지는 부분)
        item = {
            "project_id": project_id,
            "service_id": data.id,
            "user_id": user_id,
            "service_type": data.service_type,

            "runtime": data.runtime,
            "cpu": data.cpu,
            "memory": data.memory,
            "port": data.port,

            "environment_variables": data.environment_variables or {},

            "deployment_url": None,
            "created_at": now,
            "updated_at": now,
        }

        if data.service_type == "dynamic":
            # 동적일 때 추가되는 필드
            item.update(
                {
                    "start_command": data.start_command,
                    "dockerfile": data.dockerfile,
                }
            )
        else:
            # 정적일 때 추가되는 필드
            item.update(
                {
                    "build_commands": data.build_commands,
                    "build_output_dir": data.build_output_dir,
                    "node_version": data.node_version,
                }
            )

        # DynamoDB 저장
        try:
            await put_item(services_table, item)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create service: {str(e)}")

        def _to_str(value):
            if value is None:
                return None
            if isinstance(value, (Decimal, int, float)):
                return str(value)
            return value

        # 응답용 (ServiceResponse 필드에 맞게 조정)
        response_data = {
            "id": item["service_id"],
            "project_id": item["project_id"],
            "user_id": item["user_id"],
            "service_type": item["service_type"],
            "runtime": item.get("runtime"),
            "cpu": _to_str(item.get("cpu")),
            "memory": _to_str(item.get("memory")),
            "start_command": item.get("start_command"),
            "dockerfile": item.get("dockerfile"),
            "port": item.get("port"),
            "build_commands": item.get("build_commands"),
            "build_output_dir": item.get("build_output_dir"),
            "node_version": item.get("node_version"),
            "environment_variables": item.get("environment_variables"),
            "deployment_url": item.get("deployment_url"),
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }

        return ServiceResponse(**response_data)

    @staticmethod
    async def get_service(user_id: str, service_id: str, project_id: str) -> ServiceResponse:
        await ProjectService.get_project(user_id, project_id)

        try:
            item = await get_item(
                services_table,
                key={"service_id": service_id},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")

        if not item or item.get("project_id") != project_id:
            raise HTTPException(status_code=404, detail="Service not found")

        def _to_int(value):
            if isinstance(value, Decimal):
                return int(value)
            return value

        def _to_str(value):
            if value is None:
                return None
            if isinstance(value, (Decimal, int, float)):
                return str(value)
            return value

        return ServiceResponse(
            id=item["service_id"],
            project_id=item["project_id"],
            user_id=item["user_id"],
            service_type=item["service_type"],
            runtime=item.get("runtime"),
            cpu=_to_str(item.get("cpu")),
            memory=_to_str(item.get("memory")),
            port=_to_int(item.get("port")) if item.get("port") is not None else None,
            start_command=item.get("start_command"),
            dockerfile=item.get("dockerfile"),
            build_commands=item.get("build_commands"),
            build_output_dir=item.get("build_output_dir"),
            node_version=item.get("node_version"),
            environment_variables=item.get("environment_variables"),
            deployment_url=item.get("deployment_url"),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    @staticmethod
    async def list_services(user_id: str, project_id: str) -> List[ServiceResponse]:
        await ProjectService.get_project(user_id, project_id)

        try:
            items = await query_items(
                services_table,
                key_condition_expression=Key("project_id").eq(project_id),
                index_name="project-index",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")

        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        def _to_int(value):
            if isinstance(value, Decimal):
                return int(value)
            return value

        def _to_str(value):
            if value is None:
                return None
            if isinstance(value, (Decimal, int, float)):
                return str(value)
            return value  # 이미 str이면 그대로

        services: List[ServiceResponse] = []
        for item in items:
            service = ServiceResponse(
                id=item["service_id"],
                project_id=item["project_id"],
                user_id=item["user_id"],
                service_type=item["service_type"],

                runtime=item.get("runtime"),
                cpu=_to_str(item.get("cpu")),  # ← 문자열 통일
                memory=_to_str(item.get("memory")),  # ← 문자열 통일
                port=_to_int(item.get("port")) if item.get("port") is not None else None,

                start_command=item.get("start_command"),
                dockerfile=item.get("dockerfile"),

                build_commands=item.get("build_commands"),
                build_output_dir=item.get("build_output_dir"),
                node_version=item.get("node_version"),

                environment_variables=item.get("environment_variables"),
                deployment_url=item.get("deployment_url"),
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
            services.append(service)

        return services

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
        # 1. 서비스 존재 확인 및 권한 체크
        existing_service = await ServiceService.get_service(user_id, service_id, project_id)

        # 2. 수정할 필드만 추출
        updates: dict = {}

        # 공통 리소스 정보
        if data.runtime is not None:
            updates["runtime"] = data.runtime
        if data.cpu is not None:
            updates["cpu"] = data.cpu
        if data.memory is not None:
            updates["memory"] = data.memory
        if data.port is not None:
            updates["port"] = data.port

        # dynamic 전용
        if data.start_command is not None:
            updates["start_command"] = data.start_command
        if data.dockerfile is not None:
            updates["dockerfile"] = data.dockerfile

        # static 전용
        if data.build_commands is not None:
            updates["build_commands"] = data.build_commands
        if data.build_output_dir is not None:
            updates["build_output_dir"] = data.build_output_dir
        if data.node_version is not None:
            updates["node_version"] = data.node_version

        # 공통
        if data.environment_variables is not None:
            updates["environment_variables"] = data.environment_variables

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # 4. updated_at 갱신
        updates["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # 5. DB 업데이트 - PK는 service_id 하나만 사용
        try:
            await update_item(
                services_table,
                key={"service_id": service_id},
                updates=updates,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update service: {str(e)}")

        # 6. 최종 상태 다시 조회
        return await ServiceService.get_service(user_id, service_id, project_id)

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

    @staticmethod
    async def get_service_by_id(service_id: str) -> dict:
        try:
            item = await get_item(  # get_item 헬퍼가 있다면
                services_table,
                key={"service_id": service_id},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get service: {e}")

        if not item:
            raise HTTPException(status_code=404, detail="Service not found")

        return item

    @staticmethod
    async def deploy_service(user_id: str, service_id: str) -> DeployResponse:
        """
        서비스 배포 트리거
        """
        if not DEPLOY_LAMBDA_NAME:
            raise HTTPException(status_code=500, detail="DEPLOY_LAMBDA_NAME is not configured")

        service = await ServiceService.get_service_by_id(service_id)

        service_type = service.get("service_type")

        base_payload = {
            "user_id": service["user_id"],  # ← 람다 validate_parameters 에서 필수
            "project_id": service["project_id"],
            "service_id": service_id,
            "service_type": service_type,
            "runtime": service.get("runtime"),
            "port": service.get("port"),
            "environment_variables": service.get("environment_variables") or {},
        }

        if service_type == "static":
            payload = {
                **base_payload,
                "build_commands": service.get("build_commands", []),
                "build_output_dir": service.get("build_output_dir"),
                "node_version": service.get("node_version"),
            }
        else:
            payload = {
                **base_payload,
                "cpu": service.get("cpu"),
                "memory": service.get("memory"),
                "start_command": service.get("start_command"),
                "dockerfile": service.get("dockerfile"),
            }

        # Decimal → int 로 변환 (JSON 직렬화용)
        def _sanitize_for_json(obj):
            if isinstance(obj, Decimal):
                # cpu/memory/port 같은 건 정수라 int로 변환
                return int(obj)
            if isinstance(obj, dict):
                return {k: _sanitize_for_json(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_sanitize_for_json(v) for v in obj]
            return obj

        payload = _sanitize_for_json(payload)

        try:
            resp = lambda_client.invoke(
                FunctionName=DEPLOY_LAMBDA_NAME,
                InvocationType="Event",  # 비동기
                Payload=json.dumps(payload).encode("utf-8"),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to invoke deploy lambda: {e}")

        request_id = resp.get("ResponseMetadata", {}).get("RequestId")

        return DeployResponse(
            service_id=service_id,
            service_type=service_type,
            status="queued",
            lambda_request_id=request_id,
        )
