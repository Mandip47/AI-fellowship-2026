FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p logs && echo "[]" > logs/query_logs.json

EXPOSE 8501

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
