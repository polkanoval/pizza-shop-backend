from django.http import JsonResponse
from django.db import connection
from django_redis import get_redis_connection

# 1. Хесчек Базы Данных (SQLite)
def health_db(request):
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok", "service": "database"}, status=200)
    except Exception:
        # Важно: при ошибке возвращаем 500, но чистый JSON, без трейсбеков в ответе
        return JsonResponse({"status": "error", "service": "database"}, status=500)

# 2. Хесчек Ботов (Redis/Celery Broker)
def health_bots(request):
    try:
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        return JsonResponse({"status": "ok", "service": "redis_bots"}, status=200)
    except Exception:
        return JsonResponse({"status": "error", "service": "redis_bots"}, status=500)

# 3. Хесчек Фронтенда/API Liveness Probe
def health_frontend(request):
    # Просто подтверждаем, что Django-процесс жив и готов отвечать базовые запросы
    return JsonResponse({"status": "ok", "service": "frontend_api"}, status=200)

