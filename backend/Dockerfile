# 1. Используем slim-версию (она легче обычной, но стабильнее alpine для Python)
FROM python:3.12-slim

# 2. Устанавливаем системные зависимости
# Добавлена очистка кэша apt (rm -rf ...), чтобы образ весил еще меньше
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 3. Настройка переменных окружения
# Python не будет создавать файлы .pyc и будет сразу выводить логи в консоль
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 4. Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем код
COPY . .

# 6. Запуск
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]