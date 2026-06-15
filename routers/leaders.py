from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.task import TaskModel
from schemas.leader import LeaderCreate, LeaderLogin
from database.database import get_db
from models.leader import LeaderModel
from schemas.task import TaskStatus, TaskCreate
from tools.password import hash_password, verify_password
from tools.authentication import create_access_token, get_current_leader
from uuid import uuid4
from models.user import UserModel
from schemas.user import UserCreate
from tools.helper import checkAllUsersExists
from database.redis_db import get_redis
from redis.asyncio import Redis

leadersRouter = APIRouter(prefix="/leaders")


@leadersRouter.get("/fetchreport")
def fetchReport(
    db: Session = Depends(get_db), Leader_details=Depends(get_current_leader)
):
    try:
        tasks = (
            db.query(TaskModel)
            .filter(TaskModel.assigned_by == Leader_details[0].email)
            .all()
        )
        report = {}
        for task in tasks:
            if task.status.lower() not in report:
                report[task.status.lower()] = 0
            report[task.status.lower()] += 1
        return report
    except Exception as e:
        return {"error": e}


@leadersRouter.post("/createleader")
def createLeader(leader_details: LeaderCreate, db: Session = Depends(get_db)):
    try:
        existing = (
            db.query(LeaderModel)
            .filter(LeaderModel.email == leader_details.email)
            .first()
        )
        if existing:
            return {"error": "email already exists"}

        hashed_password = hash_password(leader_details.password)
        db_leader = LeaderModel(
            leader_id=str(uuid4()),
            name=leader_details.name,
            email=leader_details.email,
            password=hashed_password,
        )

        db.add(db_leader)
        db.commit()
        db.refresh(db_leader)
        return {"message": "leader created", "leader": db_leader.leader_id}

    except Exception as e:
        db.rollback()
        return {"error": "not able to create  leader"}


@leadersRouter.get("/allleader")
def fetchall(db: Session = Depends(get_db), current_leader=Depends(get_current_leader)):
    try:
        return {"message": db.query(LeaderModel).all()}
    except Exception as e:
        return {"error": "not able to fetch leaders"}


@leadersRouter.post("/updatetaskstatus")
def updateTaskStatus(
    task_details: TaskStatus,
    db: Session = Depends(get_db),
    current_leader=Depends(get_current_leader),
):
    try:
        task = (
            db.query(TaskModel)
            .filter(TaskModel.task_id == task_details.task_id)
            .first()
        )
        if not task:
            return {"error": "task not exist"}

        if task.assigned_by != current_leader[0].email:
            return {"error": "task not created by you"}

        task.status = str(task_details.newStatus.value)
        db.commit()
        db.refresh(task)
        return {"message": "sucessfully update task"}
    except Exception as e:
        return {"error": "not able to update status"}


@leadersRouter.post("/createtask")
def createTask(
    task_details: TaskCreate,
    db: Session = Depends(get_db),
    current_leader=Depends(get_current_leader),
):
    usersEmails = task_details.assigned_to
    found, notFound = checkAllUsersExists(usersEmails, db)
    if notFound:
        return {"error": "some users not exists", "list": notFound}

    try:
        db_task = TaskModel(
            task_id=str(uuid4()),
            title=task_details.title,
            description=task_details.description,
            assigned_to=found,
            assigned_by=current_leader[0].email,
            status=task_details.status,
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        return {"message": "succesfully created task", "taskid": db_task.task_id}

    except Exception as e:
        return {"error": "not able to create task"}


@leadersRouter.get("/alltasks")
def fetchalltasks(
    db: Session = Depends(get_db), current_leader=Depends(get_current_leader)
):
    try:
        return {
            "message": db.query(TaskModel)
            .filter(TaskModel.assigned_by == current_leader[0].email)
            .all()
        }
    except Exception as e:
        return {"error": "not able to fetch tasks"}


@leadersRouter.post("/createuser")
def createUser(
    user_details: UserCreate,
    db: Session = Depends(get_db),
    current_leader=Depends(get_current_leader),
):
    try:
        existing = (
            db.query(UserModel).filter(UserModel.email == user_details.email).first()
        )
        if existing:
            return {"error": "email already exists"}

        hashed_password = hash_password(user_details.password)
        db_user = UserModel(
            user_id=str(uuid4()),
            name=user_details.name,
            email=user_details.email,
            password=hashed_password,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"message": "user created", "userid": db_user.user_id}

    except Exception as e:
        db.rollback()
        return {"error": "not able to create user"}


@leadersRouter.get("/alluser")
def fetchalluser(
    db: Session = Depends(get_db), current_leader=Depends(get_current_leader)
):
    try:
        return {"message": db.query(UserModel).all()}
    except Exception as e:
        return {"error": "not able to fetch users"}


@leadersRouter.post("/login")
def login(leader_details: LeaderLogin, db: Session = Depends(get_db)):
    try:
        leader = (
            db.query(LeaderModel)
            .filter(LeaderModel.email == leader_details.email)
            .first()
        )
        if not leader:
            return {"error": "leader not exist"}

        if not verify_password(leader_details.password, leader.password):
            return {
                "error": "incorrect password",
            }
        token = create_access_token(leader.leader_id)
        return {"token": token}

    except Exception as e:
        return {"error": "error in login"}


@leadersRouter.post("/logout")
async def logout(
    current_leader=Depends(get_current_leader), redis: Redis = Depends(get_redis)
):
    await redis.set(
        f"blacklist:{current_leader[1]}",
        "1",
        ex=3600,
    )
    return {"message": "logout successfully", "leader": current_leader}
