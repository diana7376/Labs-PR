FROM python:3.11-slim
WORKDIR /app
COPY . /app
EXPOSE 8080
ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py", "content"]
