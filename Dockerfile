FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests gunicorn flask

COPY trader.py .
COPY requirements.txt .

# Health check
EXPOSE 3000

CMD ["python", "trader.py"]
