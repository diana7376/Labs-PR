# Use official slim Python image for smaller size and faster builds
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy all files from your project folder (including server.py and content) to the container
COPY . /app

# If you have a requirements.txt file, install dependencies
# (Uncomment below if you use requirements.txt)
# RUN pip install --no-cache-dir -r requirements.txt

# Run the server when the container starts
CMD ["python", "server.py", "content"]
