# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Firefox and the required driver
RUN apt-get update \
    && apt-get install -y firefox-esr \
    && apt-get install -y wget \
    && apt-get install -y xvfb \
    && apt-get install -y gnupg2 \
    && apt-get install -y libdbus-glib-1-2 \
    && apt-get install -y libxt6 \
    && wget -O geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz \
    && tar -xvzf geckodriver.tar.gz \
    && mv geckodriver /usr/local/bin \
    && rm geckodriver.tar.gz
    
# Copy the Python code and requirements.txt into the container
COPY main.py /app/
COPY crawler.py /app/
COPY requirements.txt /app/

# Install dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for the API key

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
