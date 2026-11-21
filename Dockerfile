# Use official Python lightweight image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY ai_chatbot/ai_chatbot/backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai_chatbot/ai_chatbot/backend ./backend
COPY ai_chatbot/ai_chatbot/frontend ./frontend

WORKDIR /app/backend

EXPOSE 5000

CMD ["python", "app.py"]
