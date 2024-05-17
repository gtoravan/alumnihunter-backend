# Use Python 3.8 image as the base
FROM python:3.8

# Set up environment variables
ENV DISPLAY=:0

# Install necessary packages including wget and software-properties-common
RUN apt-get update && apt-get install -y \
    wget \
    software-properties-common \
    xvfb \
    unzip

# Download and install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN apt-get install -y chromium-driver

# Additional libraries
RUN apt-get install -y \
    libxi6 \
    libgconf-2-4 \
    libxss1 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libgbm-dev

# Clear apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/*

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
    bs4==0.0.2 \
    webdriver-manager

# Expose the necessary port
EXPOSE 443

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443"]

# Build command (added as a comment for reference)
# sudo docker build --no-cache -t sel .
