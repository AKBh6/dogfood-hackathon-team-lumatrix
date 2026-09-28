FROM python:3.11-slim

WORKDIR /app

# Ensure output is printed directly to terminal
ENV PYTHONUNBUFFERED=1

# Copy dependency definition
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure data directory exists for SQLite storage
RUN mkdir -p /app/data

EXPOSE 8000

# Seed database first, then launch FastAPI server
CMD python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000
