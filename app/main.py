# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.routers import auth
from app.core.config import settings
from app.routers.health import router

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="GitHub-based deployment automation service",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",  # Vite
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(router)

@app.get("/")
def root():
    """Health check"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "status": "running",
        "version": "1.0.0"
    }

# Lambda Handler
handler = Mangum(app, lifespan="off")