# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Specify the version of Firefox to be installed
ENV FIREFOX_VERSION=116.0+build2-0ubuntu0.20.04.2

# Install the specified version of Firefox and its dependencies
RUN apt-get update && apt-get install -y firefox-esr=$FIREFOX_VERSION && rm -rf /var/lib/apt/lists/*

# Copy the Python code and requirements.txt into the container
COPY main.py /app/
COPY crawler.py /app/
COPY requirements.txt /app/

# Install dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for the API key

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
