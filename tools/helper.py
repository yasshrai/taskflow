from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import Depends
from database.database import get_db
from models import UserModel


# helper function
def checkAllUsersExists(
    usersEmail: List[str], db: Session = Depends(get_db)
) -> Tuple[List[str], List[str]]:
    if not usersEmail:
        return ([], [])
    notFound = []
    found = []
    for userEmail in usersEmail:
        existing = db.query(UserModel).filter(UserModel.email == userEmail).first()
        if existing:
            found.append(userEmail)
        else:
            notFound.append(userEmail)
    return (found, notFound)
