
FROM python:3.12-slim-trixie

# Copy uv binaries to the system path correctly
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for caching optimization
COPY pyproject.toml uv.lock ./

# Create virtual environment and install exact locked dependencies
RUN uv venv .venv && \
    uv sync --frozen

# Ensure subsequent steps and runtime use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Copy the rest of your application code
COPY . .

# Use 'uv run' to safely execute 'fastapi run' in production
CMD ["fastapi", "run"]
