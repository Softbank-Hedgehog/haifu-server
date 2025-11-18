#!/usr/bin/env python3
"""
DynamoDB Local 테이블 생성 스크립트

사용법:
    python scripts/create_local_tables.py

전제조건:
    - DynamoDB Local이 실행 중이어야 함 (docker-compose up -d)
    - http://localhost:8000 에서 접근 가능해야 함
"""

import boto3
from botocore.exceptions import ClientError

# 로컬 DynamoDB 연결
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='ap-northeast-2',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)


def create_projects_table():
    """Projects 테이블 생성"""
    try:
        table = dynamodb.create_table(
            TableName='haifu-projects',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},   # Partition Key
                {'AttributeName': 'project_id', 'KeyType': 'RANGE'}  # Sort Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'N'},
                {'AttributeName': 'project_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand
        )
        print(f"✅ Created table: {table.table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table 'haifu-projects' already exists")
        else:
            print(f"❌ Error creating projects table: {e}")
            raise


def create_services_table():
    """Services 테이블 생성"""
    try:
        table = dynamodb.create_table(
            TableName='haifu-services',
            KeySchema=[
                {'AttributeName': 'project_id', 'KeyType': 'HASH'},  # Partition Key
                {'AttributeName': 'service_id', 'KeyType': 'RANGE'}  # Sort Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'project_id', 'AttributeType': 'S'},
                {'AttributeName': 'service_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'N'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table.table_name}")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table 'haifu-services' already exists")
        else:
            print(f"❌ Error creating services table: {e}")
            raise


def list_tables():
    """테이블 목록 조회"""
    try:
        client = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='ap-northeast-2',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        response = client.list_tables()
        tables = response.get('TableNames', [])
        print(f"\n📋 Existing tables: {tables}")
    except Exception as e:
        print(f"❌ Error listing tables: {e}")


if __name__ == '__main__':
    print("🚀 Creating DynamoDB Local tables...")
    print("=" * 60)

    create_projects_table()
    create_services_table()

    print("=" * 60)
    print("✅ Done!")

    list_tables()
