
FROM python:3.11-slim

WORKDIR /app

COPY server.py .

# Optionally, copy your serve_directory with test files (or mount later)
# COPY serve_directory ./files


CMD ["python", "server.py", "./files"]
