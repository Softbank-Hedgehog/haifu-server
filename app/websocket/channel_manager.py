# 채널 기반 WebSocket 연결 관리 (channel_id -> set[WebSocket])

from typing import Dict, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ChannelConnectionManager:
    """
    channel_id 단위로 WebSocket 연결을 관리하는 매니저.

    여기서 channel_id는 아직 확정되지 않은 배포 식별자:
    - deployment_id 일 수도 있고
    - (user_id, project_id, service_id)를 합친 문자열일 수도 있음

    중요한 건 "같은 channel_id를 구독하는 클라이언트끼리 같은 메시지를 받는다"는 것.
    """

    def __init__(self) -> None:
        # channel_id -> set of WebSocket
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, channel_id: str, websocket: WebSocket) -> None:
        """
        새 WebSocket 연결을 받아 해당 channel에 등록
        """
        await websocket.accept()
        logger.info(f"WebSocket connected. channel_id={channel_id}")
        if channel_id not in self._connections:
            self._connections[channel_id] = set()
        self._connections[channel_id].add(websocket)

    def disconnect(self, channel_id: str, websocket: WebSocket) -> None:
        """
        채널에서 WebSocket 연결 제거
        """
        conns = self._connections.get(channel_id)
        if not conns:
            return

        if websocket in conns:
            conns.remove(websocket)
            logger.info(f"WebSocket disconnected. channel_id={channel_id}")

        if not conns:
            # 이 채널에 더 이상 연결이 없으면 dict에서 제거
            self._connections.pop(channel_id, None)

    async def send_to_channel(self, channel_id: str, message: dict) -> None:
        """
        특정 channel_id를 구독 중인 모든 클라이언트에게 메시지 전송
        """
        conns = self._connections.get(channel_id)
        if not conns:
            logger.info(f"No active WebSocket connections for channel_id={channel_id}")
            return

        disconnect_list = []

        for ws in list(conns):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to websocket. channel_id={channel_id}, error={e}")
                disconnect_list.append(ws)

        # 전송 실패한 소켓 정리
        for ws in disconnect_list:
            self.disconnect(channel_id, ws)


# 전역 싱글턴처럼 사용할 매니저 인스턴스
channel_manager = ChannelConnectionManager()
