# Use the official Ubuntu image as the base image
FROM ubuntu:20.04

# Set non-interactive environment
ENV DEBIAN_FRONTEND=noninteractive

# Update the package index and install Python and other dependencies
RUN apt-get update && apt-get install -y python3.10 python3-pip firefox

# Set the working directory in the container
WORKDIR /app

# Copy the Python code and requirements.txt into the container
COPY main.py /app/
COPY crawler.py /app/
COPY requirements.txt /app/ 

# Install dependencies specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Set the environment variable for the API key

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
