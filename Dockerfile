# Dockerfile для системы управления библиотекой
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Library Management System"
LABEL description="Containerized library management system with PostgreSQL"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    # Для PyQt5
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Для Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-rus \
    # Для PostgreSQL клиента
    libpq-dev \
    postgresql-client \
    # Утилиты
    git \
    # Для PDF (Unicode-шрифты)
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p resources/qr_codes resources/covers resources/icons temp logs

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen
ENV DISPLAY=:99

# Порт для возможного API (будущее расширение)
EXPOSE 8000

# Создание непривилегированного пользователя
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# По умолчанию запускаем тесты
CMD ["pytest", "-v"]
