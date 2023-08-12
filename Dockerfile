# Use the official Ubuntu image as the base image
FROM ubuntu:20.04

# Set non-interactive environment
ENV DEBIAN_FRONTEND=noninteractive

# Create an "app" directory
WORKDIR /app
COPY . /app

# Update the package index and install Python and other dependencies
RUN apt-get update && apt-get install -y python3.10 python3-pip firefox

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Clean up package cache
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the environment variable for the API key
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
