import os
from functools import lru_cache
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
        "https://softbank-hedgehog.github.io/haifu-client/"
    ]

    # AWS
    AWS_REGION: str = "ap-northeast-2"

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
        ssm = boto3.client("ssm", region_name='ap-northeast-2')

        def get_param(name: str) ->  str:
            try:
                response = ssm.get_parameter(Name=name, WithDecryption=True)
                return response['Parameter']['Value']
            except Exception as e:
                print(f"다음 파라미터를 가져오는데 실패했습니다: {name}: {e}")
                return ""


        return Settings(
            GITHUB_CLIENT_ID=get_param("/haifu/github-client-id"),
            GITHUB_CLIENT_SECRET=get_param("/haifu/github-client-secret"),
            JWT_SECRET_KEY=get_param("/haifu/jwt-secret"),
            FRONTEND_URL=get_param("/haifu/frontend-url"),
            ALLOWED_FRONTEND_URLS=[
                "http://localhost:3000",
                "https://softbank-hedgehog.github.io/haifu-client/"
            ]
        )
    except Exception as e:
        print(f"파라미터 스토어를 로드하는데 실패 했습니다.: {e}")
        return Settings()

settings = get_settings()
