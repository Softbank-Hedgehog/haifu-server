# 클라이언트와 실제로 WebSocket으로 통신하는 라우터

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.channel_manager import channel_manager
from app.schemas.deployment import DeploymentUpdate
from app.service.deployment_stream import push_deployment_update
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)


@router.websocket("/deployments/{channel_id}")
async def deployments_ws(
    websocket: WebSocket,
    channel_id: str,
    token: str = Query(..., description="JWT access token"),
):
    """
    배포 진행 상황을 스트리밍하는 WebSocket 엔드포인트.

    - 클라이언트는 아래와 같이 접속:
      ws://{API_BASE}/ws/deployments/{channel_id}?token=JWT

    - 여기서 channel_id는
      - deployment_id
      - 혹은 (user_id, project_id, service_id)를 encoding 한 값
      중 팀에서 나중에 정하는 값으로 사용.

    - token은 추후 JWT 검증 로직으로 연결.
    """

    # TODO: token 검증 로직 (기존 get_current_user / decode_jwt 재사용)
    # try:
    #     user = decode_jwt(token)
    # except Exception:
    #     await websocket.close(code=4401)
    #     return

    await channel_manager.connect(channel_id, websocket)

    try:
        while True:
            # 클라이언트에서 오는 메시지가 필요 없으면
            # 단순히 receive만 해서 연결 유지 (ping 용)
            await websocket.receive_text()
    except WebSocketDisconnect:
        channel_manager.disconnect(channel_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error on channel {channel_id}: {e}")
        channel_manager.disconnect(channel_id, websocket)
        await websocket.close()

@router.post("/debug/deployments/{channel_id}/ping")
async def debug_ping(channel_id: str):
    """
    Postman으로 WS 테스트할 때 쓰는 임시 HTTP 엔드포인트.
    """
    update = DeploymentUpdate(
        channel_id=channel_id,
        deployment_id="dep-debug",
        project_id="proj-debug",
        service_id="svc-debug",
        status="DEPLOYING",
        step="TEST_PING",
        message="This is a test message from debug endpoint",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )
    await push_deployment_update(update)
    return {"ok": True}