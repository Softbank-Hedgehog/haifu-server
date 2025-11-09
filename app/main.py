from fastapi import FastAPI
from app.database import Base, engine
from app.routers import users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SoftBank Hackathon Hedgehog Backend")

app.include_router(users.router)
