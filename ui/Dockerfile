FROM python:3.11-slim

WORKDIR /app

# Copy UI-specific requirements
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the whole UI folder
COPY . /app/ui

WORKDIR /app/ui

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
