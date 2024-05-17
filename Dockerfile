# Use Python 3.8 image as the base
FROM python:3.8

# Install Chromium, Chromedriver, and other necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    chromium \
    chromium-driver \
    curl \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install selenium webdriver-manager

# Set up environment variables
ENV DISPLAY=:0

# Set up the working directory
WORKDIR /app

# Copy local files to the app directory
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn==0.29.0 \
    selenium==4.20.0 \
    regex==2024.4.28 \
    bs4==0.0.2

# Expose the necessary port
EXPOSE 443

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443"]

# Build command (added as a comment for reference)
# sudo docker build --no-cache -t sel .
