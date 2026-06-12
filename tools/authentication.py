from fastapi import Depends, HTTPException
import jwt
from datetime import datetime, timedelta, timezone
from database.database import get_db
from sqlalchemy.orm import Session
import dotenv
import os
from models import LeaderModel
from fastapi.security import HTTPBearer
from models.user import UserModel

dotenv.load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET", "")
ALGORITHM = "HS256"


security = HTTPBearer()


def get_current_user(token: str, db: Session = Depends(get_db)):
    token = token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload["sub"]

    user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
    if not user:
        raise HTTPException(401, "User not Found")

    return user


def get_current_leader(
    token: str,
    db: Session = Depends(get_db),
):
    token = token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    leader_id = payload["sub"]

    leader = db.query(LeaderModel).filter(LeaderModel.leader_id == leader_id).first()

    if not leader:
        raise HTTPException(401, "leader not found")

    return leader


def create_access_token(id: str):
    payload = {
        "sub": id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
