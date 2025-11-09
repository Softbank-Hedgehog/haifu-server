from sqlalchemy import Column, Integer, String, Enum, DateTime
from app.database import Base
from datetime import datetime, timezone, timedelta
import enum

KST = timezone(timedelta(hours=9))

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class Member(Base):
    __tablename__ = "members"

    member_id = Column(String(50), primary_key=True, index=True)    # 멤버 ID, PK
    nickname = Column(String(50))                                   # 멤버 이름
    login_id = Column(String(50))                                   # 로그인 ID
    password = Column(String(255))                                  # 패스워드 (암호화된 채로 저장)
    role = Column(Enum(UserRole))                                   # 사용자 역할(ADMIN, USER)
    created_at = Column(DateTime, default=datetime.now(KST))        # 한국기준 가입시간 저장