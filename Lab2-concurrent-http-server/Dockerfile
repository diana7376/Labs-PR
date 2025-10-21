FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests

COPY concurrent_server.py ./

COPY content/ ./content/

EXPOSE 8000

CMD ["python", "concurrent_server.py", "thread-pool", "8000", "10"]