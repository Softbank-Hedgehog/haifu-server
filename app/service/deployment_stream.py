from app.websocket.channel_manager import channel_manager
from app.schemas.deployment import DeploymentUpdate


async def push_deployment_update(update: DeploymentUpdate) -> None:
    """
    서버 내부 어디에서든 호출할 수 있는 헬퍼.

    예:
    - 배포 상태 콜백 HTTP 핸들러 내부
    - 폴링 작업(watcher) 내부
    """
    payload = {
        "type": "deployment_update",
        **update.model_dump(),
    }
    await channel_manager.send_to_channel(update.channel_id, payload)

