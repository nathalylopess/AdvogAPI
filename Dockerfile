FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV CHROME_VERSION=137.0.7151.68

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libnss3 \
    libxss1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libgbm1 \
    libxrandr2 \
    libatk1.0-0 \
    xdg-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Baixa e instala o Chrome
RUN wget -O /tmp/chrome-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip && \
    unzip /tmp/chrome-linux64.zip -d /opt/ && \
    mv /opt/chrome-linux64 /opt/chrome && \
    ln -s /opt/chrome/chrome /usr/bin/google-chrome && \
    rm /tmp/chrome-linux64.zip

# Baixa e instala o ChromeDriver
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /opt/chromedriver && \
    mv /opt/chromedriver/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /opt/chromedriver

# Define caminho do Chrome
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PATH="${PATH}:/usr/local/bin"

# Cria diretório de trabalho
WORKDIR /app

# Copia o código
COPY . .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

# Cria diretório para dados do Chrome
RUN mkdir -p /tmp/chrome-data

# Define o PYTHONPATH
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]