from django.http import JsonResponse
from django.db import connection
from django_redis import get_redis_connection

def health_check(request):
    report = {
        "status": "online",
        "database": "disconnected",
        "redis": "disconnected",
    }
    try:
        connection.ensure_connection()
        report["database"] = "ok"
    except: pass

    try:
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        report["redis"] = "ok"
    except: pass

    # Если всё ок — 200, если хоть что-то упало — 500
    status_code = 200 if all(v == "ok" for k, v in report.items() if k != "status") else 500
    return JsonResponse(report, status=status_code)