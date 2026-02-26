# ==============================
# Base image (Python 3.12)
# ==============================
FROM python:3.12-slim

# ==============================
# Environment variables
# ==============================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ==============================
# Working directory
# ==============================
WORKDIR /app

# ==============================
# System dependencies
# ==============================
RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# ==============================
# Install Python dependencies
# ==============================
COPY pyproject.toml .
RUN pip install --upgrade pip \
    && pip install .

# ==============================
# Copy application source & migrations
# ==============================
COPY src/app ./app
COPY .env .env
COPY alembic.ini .
COPY migrations ./migrations

# ==============================
# Expose FastAPI port
# ==============================
EXPOSE 8000

# ==============================
# Run Alembic migrations + FastAPI
# ==============================
CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

# sudo docker build -t dfm-backend-app .
# sudo docker run -p 8082:8000 dfm-backend-app
# sudo docker tag dfm-backend-app anwaarnoaman/dfm-backend-app:1.0.2
# sudo docker push anwaarnoaman/dfm-backend-app:1.0.2

 