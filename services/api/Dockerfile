FROM python:3.11-slim

# Where our app will live in the container
WORKDIR /app

# Install dependencies
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared core code
COPY core /app/core

# Copy API app code
COPY services/api/app /app/app

# So "core" & "app" are importable as top-level packages
ENV PYTHONPATH=/app

# Run FastAPI with uvicorn, listening on all interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


