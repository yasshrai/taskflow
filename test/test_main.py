from fastapi.testclient import TestClient
import sys
import os
import pytest
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from database.database import SessionLocal
from models.user import UserModel
from models.leader import LeaderModel
from models.task import TaskModel
from database.redis_db import get_redis


# 1. Mock Redis implementation
class MockRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value

    async def exists(self, key: str):
        return key in self.store

    async def aclose(self):
        pass


# Instantiate mock redis
mock_redis_instance = MockRedis()

# Override get_redis dependency
app.dependency_overrides[get_redis] = lambda: mock_redis_instance

client = TestClient(app)


# 2. Database Cleanup Fixture
@pytest.fixture(scope="module", autouse=True)
def db_cleanup():
    # Setup - nothing to do before tests
    yield
    # Teardown - clean up test entities
    db = SessionLocal()
    try:
        db.query(TaskModel).filter(TaskModel.title.like("test_task_%")).delete(
            synchronize_session=False
        )
        db.query(UserModel).filter(UserModel.email.like("test_user_%")).delete(
            synchronize_session=False
        )
        db.query(LeaderModel).filter(LeaderModel.email.like("test_leader_%")).delete(
            synchronize_session=False
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Teardown cleanup failed: {e}")
    finally:
        db.close()


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello from task management"}


def test_welcome_user():
    response = client.get("/users/")
    assert response.status_code == 200
    assert response.json() == {"message": "welcome to users router"}


def test_leader_and_user_flows():
    # We run the end-to-end integration tests in a logical sequence to maintain clean state dependencies.
    unique_suffix = uuid.uuid4().hex[:8]

    # --- LEADER FLOW ---

    # 1. Create leader
    leader_name = f"test_leader_{unique_suffix}"
    leader_email = f"test_leader_{unique_suffix}@example.com"
    leader_password = "password123"

    create_leader_response = client.post(
        "/leaders/createleader",
        json={"name": leader_name, "email": leader_email, "password": leader_password},
    )
    assert create_leader_response.status_code == 200
    res_data = create_leader_response.json()
    assert "message" in res_data
    assert res_data["message"] == "leader created"
    assert "leader" in res_data

    # Try creating same leader again to verify conflict handling
    conflict_response = client.post(
        "/leaders/createleader",
        json={"name": leader_name, "email": leader_email, "password": leader_password},
    )
    assert conflict_response.status_code == 200
    assert conflict_response.json() == {"error": "email already exists"}

    # 2. Login leader
    login_response = client.post(
        "/leaders/login", json={"email": leader_email, "password": leader_password}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "token" in login_data
    leader_token = login_data["token"]

    # Login leader with wrong password
    wrong_pwd_response = client.post(
        "/leaders/login", json={"email": leader_email, "password": "wrongpassword"}
    )
    assert wrong_pwd_response.status_code == 200
    assert wrong_pwd_response.json() == {"error": "incorrect password"}

    # Login leader with non-existent email
    non_existent_login = client.post(
        "/leaders/login",
        json={
            "email": f"non_existent_{unique_suffix}@example.com",
            "password": leader_password,
        },
    )
    assert non_existent_login.status_code == 200
    assert non_existent_login.json() == {"error": "leader not exist"}

    # 3. Create user (via leader)
    user_name = f"test_user_{unique_suffix}"
    user_email = f"test_user_{unique_suffix}@example.com"
    user_password = "userpassword123"

    # Create user without auth should return error (it tries to call dependency get_current_leader without token)
    # Since token parameter is missing, FastAPI will reject it or return HTTP 422 Unprocessable Entity
    unauth_create_user = client.post(
        "/leaders/createuser",
        json={"name": user_name, "email": user_email, "password": user_password},
    )
    assert unauth_create_user.status_code == 422  # Missing query parameter 'token'

    # Create user with valid leader token
    create_user_response = client.post(
        f"/leaders/createuser?token={leader_token}",
        json={"name": user_name, "email": user_email, "password": user_password},
    )
    assert create_user_response.status_code == 200
    user_res_data = create_user_response.json()
    assert user_res_data["message"] == "user created"
    assert "userid" in user_res_data

    # Try creating user with duplicate email
    duplicate_user_response = client.post(
        f"/leaders/createuser?token={leader_token}",
        json={"name": user_name, "email": user_email, "password": user_password},
    )
    assert duplicate_user_response.status_code == 200
    assert duplicate_user_response.json() == {"error": "email already exists"}

    # 4. Fetch all users (via leader)
    all_users_response = client.get(f"/leaders/alluser?token={leader_token}")
    assert all_users_response.status_code == 200
    all_users_data = all_users_response.json()
    assert "message" in all_users_data
    # Check that the newly created user is in the list
    emails = [u["email"] for u in all_users_data["message"]]
    assert user_email in emails

    # 5. Fetch all leaders (via leader)
    all_leaders_response = client.get(f"/leaders/allleader?token={leader_token}")
    assert all_leaders_response.status_code == 200
    all_leaders_data = all_leaders_response.json()
    assert "message" in all_leaders_data
    leader_emails = [l["email"] for l in all_leaders_data["message"]]
    assert leader_email in leader_emails

    # --- USER FLOW ---

    # 6. Login user
    user_login_response = client.post(
        "/users/login", json={"email": user_email, "password": user_password}
    )
    assert user_login_response.status_code == 200
    user_login_data = user_login_response.json()
    assert "token" in user_login_data
    user_token = user_login_data["token"]

    # Login user wrong password
    user_wrong_login = client.post(
        "/users/login", json={"email": user_email, "password": "wrongpassword"}
    )
    assert user_wrong_login.status_code == 200
    assert user_wrong_login.json() == {"message": "incorrect password"}

    # Login user non-existent email
    user_non_exist_login = client.post(
        "/users/login",
        json={
            "email": f"non_existent_u_{unique_suffix}@example.com",
            "password": user_password,
        },
    )
    assert user_non_exist_login.status_code == 200
    assert user_non_exist_login.json() == {"message": "user not found"}

    # --- TASK FLOW (LEADER & USER) ---

    # 7. Create task (via leader)
    task_title = f"test_task_{unique_suffix}"
    task_desc = "Implement unit tests for routers"
    create_task_response = client.post(
        f"/leaders/createtask?token={leader_token}",
        json={
            "title": task_title,
            "description": task_desc,
            "status": "created",
            "assigned_to": [user_email],
        },
    )
    assert create_task_response.status_code == 200
    task_data = create_task_response.json()
    assert task_data["message"] == "succesfully created task"
    assert "taskid" in task_data
    task_id = task_data["taskid"]

    # Try creating task for non-existent users
    invalid_task_response = client.post(
        f"/leaders/createtask?token={leader_token}",
        json={
            "title": task_title,
            "description": task_desc,
            "status": "created",
            "assigned_to": [f"non_existent_{unique_suffix}@example.com"],
        },
    )
    assert invalid_task_response.status_code == 200
    assert invalid_task_response.json()["error"] == "some users not exists"

    # 8. Fetch report (via leader)
    report_response = client.get(f"/leaders/fetchreport?token={leader_token}")
    assert report_response.status_code == 200
    report_data = report_response.json()
    # "created" status count should be >= 1
    assert report_data.get("created", 0) >= 1

    # 9. Fetch all tasks (via leader)
    all_tasks_response = client.get(f"/leaders/alltasks?token={leader_token}")
    assert all_tasks_response.status_code == 200
    all_tasks_data = all_tasks_response.json()
    assert "message" in all_tasks_data
    task_ids = [t["task_id"] for t in all_tasks_data["message"]]
    assert task_id in task_ids

    # 10. Fetch task (via user)
    user_tasks_response = client.get(f"/users/fetchtasks?token={user_token}")
    assert user_tasks_response.status_code == 200
    user_tasks_data = user_tasks_response.json()
    assert "alltask" in user_tasks_data
    user_task_ids = [t["task_id"] for t in user_tasks_data["alltask"]]
    assert task_id in user_task_ids

    # 11. Update task (via user)
    updated_title = f"{task_title}_updated"
    updated_desc = "Implement unit tests and mock dependencies"
    update_task_response = client.put(
        f"/users/updatetask?token={user_token}",
        json={
            "task_id": task_id,
            "title": updated_title,
            "description": updated_desc,
            "status": "pending",
        },
    )
    assert update_task_response.status_code == 200
    update_task_data = update_task_response.json()
    assert update_task_data["message"] == "Task updated successfully"
    assert update_task_data["task"]["title"] == updated_title
    assert update_task_data["task"]["description"] == updated_desc
    assert update_task_data["task"]["status"] == "pending"

    # Try updating non-existent task
    non_existent_update = client.put(
        f"/users/updatetask?token={user_token}",
        json={"task_id": "non_existent_task_id", "title": "dummy", "status": "pending"},
    )
    assert non_existent_update.status_code == 200
    assert non_existent_update.json() == {"message": "not task found with this id"}

    # 12. Update task status (via leader)
    update_status_response = client.post(
        f"/leaders/updatetaskstatus?token={leader_token}",
        json={"task_id": task_id, "newStatus": "completed"},
    )
    assert update_status_response.status_code == 200
    assert update_status_response.json() == {"message": "sucessfully update task"}

    # Verify task status is indeed completed
    final_tasks_response = client.get(f"/leaders/alltasks?token={leader_token}")
    final_tasks = final_tasks_response.json()["message"]
    updated_task = next(t for t in final_tasks if t["task_id"] == task_id)
    assert updated_task["status"] == "completed"

    # --- LOGOUT FLOW ---

    # 13. Logout user
    user_logout_response = client.post(f"/users/logout?token={user_token}")
    assert user_logout_response.status_code == 200
    assert user_logout_response.json()["message"] == "succesfully logout"

    # 14. Logout leader
    leader_logout_response = client.post(f"/leaders/logout?token={leader_token}")
    assert leader_logout_response.status_code == 200
    assert leader_logout_response.json()["message"] == "logout successfully"

    # Verify blacklisted token results in 401 error
    revoked_user_response = client.get(f"/users/fetchtasks?token={user_token}")
    assert revoked_user_response.status_code == 401
    assert revoked_user_response.json()["detail"] == "Token revoked"
