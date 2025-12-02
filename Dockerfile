FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy application with correct structure
COPY backend ./backend
COPY frontend ./frontend

# Create directory for SQLite database
RUN mkdir -p /data

# Expose port
EXPOSE 8765

# Run with uvicorn - use backend.app.main path
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8765"]
