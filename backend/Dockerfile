FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy only the dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies directly via pip
# This bypasses the "Invalid statement" error in the poetry install command
RUN pip install --no-cache-dir --user "fastapi>=0.110.0" "uvicorn>=0.27.0" "sqlalchemy>=2.0.0" "psycopg>=3.1.0" "alembic>=1.13.0" "pydantic-settings>=2.2.0" "httpx>=0.27.0" "python-jose[cryptography]>=3.3.0" "passlib==1.7.4" "bcrypt<4.0.0" "greenlet>=3.0.0" "asyncpg>=0.29.0" "jinja2>=3.1.0" "python-multipart>=0.0.12"

ENV PYTHONPATH=/app
COPY . /app/backend

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]