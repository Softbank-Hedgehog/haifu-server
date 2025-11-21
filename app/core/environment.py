# app/core/environment.py
import os
from app.core.config import settings


class Environment:
    """환경 감지 및 관리 유틸리티"""
    
    @staticmethod
    def is_lambda() -> bool:
        """Lambda 환경인지 확인"""
        return (
            os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None or
            os.getenv("AWS_EXECUTION_ENV") is not None or
            os.getenv("LAMBDA_RUNTIME_DIR") is not None or
            "lambda" in os.getenv("AWS_EXECUTION_ENV", "").lower()
        )
    
    @staticmethod
    def is_local() -> bool:
        """로컬 개발 환경인지 확인"""
        return (
            settings.ENVIRONMENT == "local" or
            not Environment.is_lambda()
        )
    
    @staticmethod
    def get_backend_url() -> str:
        """현재 환경에 맞는 백엔드 URL 반환"""
        if Environment.is_lambda():
            return "https://b2s3zdwgbpxjbkbyhfzi4tolqq0igzuo.lambda-url.ap-northeast-2.on.aws"
        else:
            return "http://localhost:8001"
    
    @staticmethod
    def get_environment_name() -> str:
        """현재 환경 이름 반환"""
        return "lambda" if Environment.is_lambda() else "local"