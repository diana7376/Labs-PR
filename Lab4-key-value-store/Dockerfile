# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Flask and requests
RUN pip install flask requests

# Copy all files to the container
COPY . /app

# Expose ports for leader and followers
EXPOSE 8000
EXPOSE 8001
EXPOSE 8002
EXPOSE 8003
EXPOSE 8004
EXPOSE 8005

# Choose entry point based on ROLE environment variable
CMD ["sh", "-c", "if [ \"$ROLE\" = \"leader\" ]; then python leader.py; else python follower.py; fi"]
