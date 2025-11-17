FROM python:3.11-slim

WORKDIR /workspace

# Install deps
COPY services/ingest/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared core code
COPY core /workspace/core

# Copy ingestion script
COPY services/ingest/ingest.py /workspace/ingest.py

ENV PYTHONPATH=/workspace

ENTRYPOINT ["python", "ingest.py"]
