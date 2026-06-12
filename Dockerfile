FROM python:3.12-slim-trixie

# Copy the uv and uvx binaries from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# CRITICAL FIX: Directs Docker to look inside your virtual environment for commands
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies using uv with local caching enabled
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

EXPOSE 8000

# Copy your source code AFTER dependencies are installed
COPY . .

# Final fast sync to register your project packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Use 'run' instead of 'dev' for container deployments
CMD ["fastapi", "run", "main.py", "--port", "8000"]

