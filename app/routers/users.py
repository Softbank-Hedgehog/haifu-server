from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
import uuid

router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 회원 가입 API
@router.post("/signup", response_model=schemas.MemberResponse)
def signup(user: schemas.MemberCreate, db: Session = Depends(get_db)):
    # login_id 중복 확인
    existing = db.query(models.Member).filter(models.Member.login_id == user.login_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Login ID already exists")

    # member_id 자동 생성
    generated_id = f"mem_{uuid.uuid4().hex[:8]}"

    new_member = models.Member(
        member_id=generated_id,
        login_id=user.login_id,
        nickname=user.nickname,
        password=hash_password(user.password),
        role=models.UserRole.USER
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

# 로그인 API
@router.post("/login")
def login(user: schemas.MemberLogin, db: Session = Depends(get_db)):
    # 로그인 아이디로 사용자 검색
    db_user = db.query(models.Member).filter(models.Member.login_id == user.login_id).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # JWT 생성 (payload에 member_id 포함)
    token = create_access_token({"member_id": db_user.member_id})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.MemberResponse)
def get_my_info(current_user: models.Member = Depends(get_current_user)):
    return current_user

