from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import users, health

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SoftBank Hackathon Hedgehog Backend")

# 허용할 Origin 목록
origins = [
    "http://localhost:3000",   # 로컬 React 개발 환경
    "http://127.0.0.1:3000",
    "https://hackathon-hedgehog-frontend.com"  # 실제 배포 시 프런트 도메인
]

# CORS 미들웨어 등록
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 접근을 허용할 Origin 리스트
    allow_credentials=True,           # 쿠키 등 자격 증명 허용 여부
    allow_methods=["*"],              # 허용할 HTTP 메서드
    allow_headers=["*"],              # 허용할 헤더
)

app.include_router(health.router)
