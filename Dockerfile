FROM public.ecr.aws/lambda/python:3.10

# 작업 디렉토리 설정
WORKDIR ${LAMBDA_TASK_ROOT}

# Install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ${LAMBDA_TASK_ROOT}/app/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

# ENTRYPOINT 명시
ENTRYPOINT ["/lambda-entrypoint.sh"]

# Handler
CMD ["lambda_function.lambda_handler"]