# TaskFlow

A task management API where leaders assign work to users and track progress.

Built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

## Features

- **Leaders** — create tasks, assign users, update status, view reports
- **Users** — view assigned tasks and update their work
- **Auth** — JWT-based login for leaders and users
- **Passwords** — hashed with bcrypt

## Requirements

- Python 3.13+
- PostgreSQL
- [uv](https://docs.astral.sh/uv/) (recommended)

## Setup

1. Clone the repo and install dependencies:

```bash
uv sync
```

2. Create a PostgreSQL database:

```bash
createdb taskmanage
```

3. Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://<user>@localhost:5432/taskmanage
JWT_SECRET=<your-secret-key>
REDIS_HOST="localhost"
REDIS_PORT="6379"
```
4. activate venv:
```bash
source .venv/bin/activate

```

5. Start the server:

```bash
fastapi dev
```

The API runs at `http://127.0.0.1:8000`. Interactive docs: `http://127.0.0.1:8000/docs`.
