from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session
from models.user import UserModel
from models.task import TaskModel
from database.database import get_db
from schemas.task import TaskUpdate
from schemas.user import UserChangePassword, UserLogin
from tools.authentication import create_access_token, get_current_user
from tools.password import hash_password, verify_password
from redis.asyncio import Redis
from database.redis_db import get_redis

userRouter = APIRouter(prefix="/users")


@userRouter.get("/")
def welcome():
    return {"message": "welcome to users router"}


@userRouter.get("/fetchtasks")
def fetchTask(db: Session = Depends(get_db), user_details=Depends(get_current_user)):
    if "error" in user_details:
        return {"error": str(user_details["error"])}
    tasks = (
        db.query(TaskModel)
        .filter(TaskModel.assigned_to.any(user_details["data"][0].email))
        .all()
    )
    return {"alltask": tasks}


@userRouter.put("/updatetask")
def updateTask(
    task_details: TaskUpdate,
    db: Session = Depends(get_db),
    user_details=Depends(get_current_user),
):
    if "error" in user_details:
        return {"error": str(user_details["error"])}
    try:
        task = (
            db.query(TaskModel)
            .filter(
                TaskModel.task_id == task_details.task_id,
                TaskModel.assigned_to.contains([user_details["data"][0].email]),
            )
            .first()
        )
        if not task:
            return {"message": "not task found with this id"}

        db.query(TaskModel).filter(TaskModel.task_id == task_details.task_id).update(
            {
                "status": task_details.status.value,
                "title": task_details.title,
                "description": task_details.description,
            }
        )

        db.commit()
        task = (
            db.query(TaskModel)
            .filter(TaskModel.task_id == task_details.task_id)
            .first()
        )

        return {"message": "Task updated successfully", "task": task}

    except Exception as e:
        return {"error": "error occurred"}


@userRouter.post("/changepassword")
def userchangePassword(
    change_password_details: UserChangePassword,
    db: Session = Depends(get_db),
    user_details=Depends(get_current_user),
):
    try:

        if not verify_password(
            change_password_details.oldpassword, user_details["data"][0].password
        ):
            return {"message": "incorrect passsword"}
        hashed_password = hash_password(change_password_details.newpassword)

        db.query(UserModel).filter(
            UserModel.user_id == user_details["data"][0].user_id
        ).update({"password": hashed_password})

        db.commit()
        return {"message": "succesfully change password"}
    except Exception as e:
        return {"error": e}


@userRouter.post("/login")
def login(user_details: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(UserModel).filter(UserModel.email == user_details.email).first()
        if not user:
            return {"message": "user not found"}

        if not verify_password(user_details.password, user.password):
            return {"message": "incorrect password"}

        token = create_access_token(user.user_id)
        return {"token": token}
    except Exception as e:
        return {"message": "not able to find user"}


@userRouter.post("/logout")
async def logout(
    user_details=Depends(get_current_user), redis: Redis = Depends(get_redis)
):
    if "error" in user_details:
        return {"error": str(user_details["error"])}
    await redis.set(
        f"blacklist:{user_details['data'][1]}",
        "1",
        ex=3600,
    )
    return {"message": "succesfully logout", "user": user_details["data"][0]}
