# app/core/logging.py
import logging
import sys
from app.core.environment import Environment


def setup_logging():
    """로깅 설정"""
    # 로그 레벨 설정 (환경에 따라)
    log_level = logging.DEBUG if Environment.is_local() else logging.INFO
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 핸들러 설정
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 반환"""
    return logging.getLogger(name)


# 앱 시작 시 로깅 설정
setup_logging()