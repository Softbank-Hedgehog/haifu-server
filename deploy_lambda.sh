#!/bin/bash

# AWS Lambda 배포 스크립트

echo "Lambda 배포 패키지 생성 중"

# 임시 디렉토리 생성
mkdir -p lambda_package
cd lambda_package

# 의존성 설치
echo "의존성 설치 중..."
pip install -r ../requirements.txt -t .

# 애플리케이션 코드 복사
echo "애플리케이션 코드 복사 중..."
cp -r ../app .
cp ../lambda_handler.py .

# ZIP 파일 생성
echo "ZIP 파일 생성 중..."
zip -r ../lambda_function.zip .

cd ..
rm -rf lambda_package

echo "배포 패키지 생성 완료: lambda_function.zip"