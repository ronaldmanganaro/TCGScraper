FROM python:3.11.12-slim-bullseye

ENV PYTHONUNBUFFERED=1

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/list/*

# Install Chrome Driver
 RUN wget -O /tmp/chromedriver_linux64.zip https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.85/linux64/chromedriver-linux64.zip && \
     unzip -o /tmp/chromedriver_linux64.zip -d /usr/local/bin

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip libnss3 libgconf-2-4 libx11-xcb1 libxcomposite1 \
    libxcursor1 libxi6 libxrandr2 libasound2 libatk1.0-0 \
    libpangocairo-1.0-0 libxss1 libgtk-3-0 libgbm1

# Install Chrome
RUN wget -O /tmp/chrome_linux64.zip https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.85/linux64/chrome-linux64.zip && \
    unzip -o /tmp/chrome_linux64.zip -d /usr/local/bin && \
    ln -s /usr/local/bin/chrome-linux64/chrome /usr/bin/google-chrome

# Ensure Chrome is on PATH
ENV PATH="/usr/local/bin/chrome-linux64:$PATH"

# Install Python dependencies
COPY /app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app ./app
WORKDIR ./app

ENTRYPOINT ["python3", "scripts/watch.py"]
