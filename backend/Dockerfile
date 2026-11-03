FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy only the dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies directly via pip
# This bypasses the "Invalid statement" error in the poetry install command
RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app
COPY . /app/backend

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]