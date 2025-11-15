# lambda_function.py
from app.main import handler

# Lambda가 찾을 수 있도록 함수로 래핑
def lambda_handler(event, context):
    return handler(event, context)