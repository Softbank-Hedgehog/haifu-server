# app/routers/source_snapshot.py
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.schemas.source_snapshot import SourceSnapshotRequest, SourceSnapshotResponse
from app.service.source_snapshot_service import (
    create_source_snapshot,
    SourceSnapshotServiceError,
)
from app.core.security import get_current_user  # 실제 경로는 프로젝트에 맞게

router = APIRouter(
    prefix="/source-snapshots",
    tags=["source-snapshots"],
)


@router.post("", response_model=SourceSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    body: SourceSnapshotRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    레포/브랜치/소스경로 기준으로 소스 파일을 S3에 업로드하고,
    업로드된 S3 prefix를 반환한다.
    """
    user_id = current_user["user_id"]

    try:
        # requests, tarfile, boto3 같이 I/O 많은 작업이 있어서
        # run_in_threadpool로 돌려주는 게 안전함
        result = await run_in_threadpool(create_source_snapshot, user_id, body)
        return result

    except SourceSnapshotServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 예상 못 한 에러는 500
        raise HTTPException(status_code=500, detail=str(e))
