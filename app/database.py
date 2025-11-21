import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_dynamodb_resource():
    """
    환경에 따라 DynamoDB resource 반환
    - 로컬: DynamoDB Local (http://localhost:8000)
    - 프로덕션: AWS DynamoDB
    """
    if settings.DYNAMODB_ENDPOINT:
        # 로컬 환경: DynamoDB Local 사용
        logger.info(f"Using DynamoDB Local at {settings.DYNAMODB_ENDPOINT}")
        return boto3.resource(
            'dynamodb',
            endpoint_url=settings.DYNAMODB_ENDPOINT,
            region_name=settings.AWS_REGION,
            aws_access_key_id='dummy',  # 로컬에서는 더미 값
            aws_secret_access_key='dummy'
        )
    else:
        # 프로덕션 환경: 실제 AWS DynamoDB
        logger.info(f"Using AWS DynamoDB in region {settings.AWS_REGION}")
        return boto3.resource(
            'dynamodb',
            region_name=settings.AWS_REGION
        )


# DynamoDB resource 및 테이블 참조
dynamodb = get_dynamodb_resource()
projects_table = dynamodb.Table(settings.DYNAMODB_PROJECTS_TABLE)
services_table = dynamodb.Table(settings.DYNAMODB_SERVICES_TABLE)


# =============================================================================
# 헬퍼 함수들
# =============================================================================

async def get_item(table, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    아이템 조회

    Args:
        table: DynamoDB Table 객체
        key: Primary Key (예: {"user_id": 123, "project_id": "abc"})

    Returns:
        조회된 아이템 또는 None
    """
    response = table.get_item(Key=key)
    return response.get('Item')


async def put_item(table, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    아이템 저장

    Args:
        table: DynamoDB Table 객체
        item: 저장할 아이템

    Returns:
        저장된 아이템
    """
    table.put_item(Item=item)
    return item


async def update_item(table, key: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    아이템 업데이트

    Args:
        table: DynamoDB Table 객체
        key: Primary Key
        updates: 업데이트할 필드들 (예: {"name": "New Name", "updated_at": "2025-11-18T10:00:00Z"})

    Returns:
        업데이트된 아이템
    """
    # UpdateExpression 생성
    update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
    expr_attr_names = {f"#{k}": k for k in updates.keys()}
    expr_attr_values = {f":{k}": v for k, v in updates.items()}

    response = table.update_item(
        Key=key,
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="ALL_NEW"
    )
    return response.get('Attributes')


async def delete_item(table, key: Dict[str, Any]) -> bool:
    """
    아이템 삭제

    Args:
        table: DynamoDB Table 객체
        key: Primary Key

    Returns:
        삭제 성공 여부
    """
    table.delete_item(Key=key)
    return True


async def query_items(
    table,
    key_condition_expression,
    index_name: Optional[str] = None,
    filter_expression=None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    쿼리 (인덱스 사용)

    Args:
        table: DynamoDB Table 객체
        key_condition_expression: Key 조건 (예: Key('user_id').eq(123))
        index_name: GSI 이름 (선택)
        filter_expression: 필터 조건 (선택)
        **kwargs: 추가 파라미터

    Returns:
        조회된 아이템 리스트
    """
    params = {
        'KeyConditionExpression': key_condition_expression,
        **kwargs
    }

    if index_name:
        params['IndexName'] = index_name

    if filter_expression:
        params['FilterExpression'] = filter_expression

    response = table.query(**params)
    return response.get('Items', [])


async def scan_items(
    table,
    filter_expression=None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    전체 스캔 (성능 주의 - 가능하면 query 사용 권장)

    Args:
        table: DynamoDB Table 객체
        filter_expression: 필터 조건 (선택)
        **kwargs: 추가 파라미터

    Returns:
        조회된 아이템 리스트
    """
    params = kwargs

    if filter_expression:
        params['FilterExpression'] = filter_expression

    response = table.scan(**params)
    return response.get('Items', [])
