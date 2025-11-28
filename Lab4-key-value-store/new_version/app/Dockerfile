FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Use host 0.0.0.0 to ensure accessibility within Docker network
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]