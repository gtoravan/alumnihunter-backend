ARG PORT=443

FROM cypress/browsers:latest


# Install necessary packages including curl
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    python3 \
    python3-pip

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install specific version of ChromeDriver
RUN CHROME_DRIVER_VERSION="124.0.6367.155" \
    && wget -N "http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip" -P ~/ \
    && unzip ~/chromedriver_linux64.zip -d ~/ \
    && rm ~/chromedriver_linux64.zip \
    && mv -f ~/chromedriver /usr/local/bin/chromedriver \
    && chown root:root /usr/local/bin/chromedriver \
    && chmod 0755 /usr/local/bin/chromedriver


# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set PATH environment variable
ENV PATH /home/root/.local/bin:${PATH}

# Copy application code
COPY . .

# Command to start Uvicorn with the application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
