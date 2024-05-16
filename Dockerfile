# Use Python 3.8 image as the base
FROM python:3.8

# Install Chromium, Chromedriver, and other necessary packages
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4

# Set up environment variables
ENV DISPLAY=:99

# Set up the working directory
WORKDIR /app

# Copy local files to the app directory
COPY . /app


# Install Python dependencies
RUN pip install annotated-types==0.6.0 \
    fastapi==0.109.0 \
    uvicorn==0.29.0 \
    selenium==4.20.0 \
    regex==2024.4.28 \
    bs4==0.0.2

# Expose the necessary port
EXPOSE 443

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443"]

# sudo docker build --no-cache -t sel .
