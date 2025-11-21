# app/schemas/deployment.py
# 나중에 람다/배포 시스템이 FastAPI로 상태 콜백을 줄 때 사용할 Pandatic 모델

from pydantic import BaseModel, Field
from typing import Optional


class DeploymentUpdate(BaseModel):
    """
    WebSocket으로 흘러갈 배포 상태 정보 형식 (초안)
    추후에 바뀔 수 있음
    """
    channel_id: str = Field(..., description="이 업데이트를 보낼 WebSocket 채널 ID")
    deployment_id: Optional[str] = Field(None, description="배포 실행 ID")
    project_id: Optional[str] = None
    service_id: Optional[str] = None
    status: str = Field(..., description="PENDING / DEPLOYING / SUCCESS / FAILED 등")
    step: Optional[str] = Field(None, description="세부 단계 식별자 (예: ECS_SERVICE_CREATING)")
    message: Optional[str] = Field(None, description="UI에 보여줄 메시지")
    timestamp: str = Field(..., description="ISO8601 형식의 시간 문자열")
