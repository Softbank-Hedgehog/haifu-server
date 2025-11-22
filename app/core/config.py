import os
from functools import lru_cache
import json
import boto3
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "hAIfu Server"
    DEBUG: bool = False
    ENVIRONMENT: str = "local"

    # 깃헙 OAuth2 정보
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # JWT 관련 정보
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_FRONTEND_URLS: list = [
        "http://localhost:3000",
        "https://softbank-hedgehog.github.io",
        "https://softbank-hedgehog.github.io/haifu-client",
        "https://d1yacqe3a2p57p.cloudfront.net",
    ]

    # AWS
    AWS_REGION: str = "ap-northeast-2"

    # Server
    PORT: int = 8000

    # DynamoDB
    DYNAMODB_ENDPOINT: str = ""  # 로컬이면 http://localhost:8000, 프로덕션이면 비워둠
    DYNAMODB_PROJECTS_TABLE: str = "haifu-projects"
    DYNAMODB_SERVICES_TABLE: str = "haifu-services"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    # Lambda: Parameter Store 사용
    try:
        secrets_client = boto3.client("secretsmanager", region_name="ap-northeast-2")
        secret_name = "haifu-server-main"

        # Secrets Manager에서 한 번만 가져오기
        response = secrets_client.get_secret_value(SecretId=secret_name)

        if "SecretString" in response:
            secret_str = response["SecretString"]
        else:
            # 혹시 Binary로 저장돼 있으면
            import base64
            secret_str = base64.b64decode(response["SecretBinary"]).decode("utf-8")

        secret_dict = json.loads(secret_str)

        # 여기서부터는 이름으로 꺼내 쓰기
        def get_secret(key: str) -> str:
            return secret_dict.get(key, "")

        return Settings(
            GITHUB_CLIENT_ID=get_secret("GITHUB_CLIENT_ID"),
            GITHUB_CLIENT_SECRET=get_secret("GITHUB_CLIENT_SECRET"),
            JWT_SECRET_KEY=get_secret("JWT_SECRET_KEY"),
            FRONTEND_URL=get_secret("FRONTEND_URL"),
            ALLOWED_FRONTEND_URLS=[
                "http://localhost:3000",
                "https://softbank-hedgehog.github.io",
                "https://softbank-hedgehog.github.io/haifu-client",
                "https://d1yacqe3a2p57p.cloudfront.net",
                "http://haifu.cloud",
                "https://haifu.cloud"
            ],
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to load secret manager: {e}")
        return Settings()

settings = get_settings()
