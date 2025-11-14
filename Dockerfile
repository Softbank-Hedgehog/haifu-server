FROM public.ecr.aws/lambda/python:3.10

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app

# Command for Lambda handler (app/main.py 내부에 handler 있어야 함)
CMD ["app.main.handler"]
