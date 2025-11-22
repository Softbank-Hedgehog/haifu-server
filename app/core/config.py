import os
from functools import lru_cache
import json
import boto3
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "hAIfu Server"
    DEBUG: bool = False

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET")
    # JWT 설정
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
    # 앱 설정
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    PORT: int = int(os.getenv("PORT", "8000"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")

    # Frontend
    ALLOWED_FRONTEND_URLS: list = [
        "http://localhost:3000",
        "https://softbank-hedgehog.github.io",
        "https://softbank-hedgehog.github.io/haifu-client",
        "https://d1yacqe3a2p57p.cloudfront.net",
        "http://haifu.cloud",
        "https://haifu.cloud"
    ]

    # AWS
    AWS_REGION: str = "ap-northeast-2"

    # DynamoDB Table
    DYNAMODB_ENDPOINT: str = ""  # 로컬이면 http://localhost:8000, 프로덕션이면 비워둠
    DYNAMODB_PROJECTS_TABLE: str = "haifu-projects"
    DYNAMODB_SERVICES_TABLE: str = "haifu-services"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
