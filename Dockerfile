# Use the official Python image as the base image
FROM python:3.10.7-slim

# Set the working directory in the container
WORKDIR /app

# Update the package index
RUN apt-get update

# Install Firefox
RUN apt-get install -y firefox 

# Copy the Python code and requirements.txt into the container
COPY main.py /app/
COPY crawler.py /app/
COPY requirements.txt /app/

# Install dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for the API key

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
