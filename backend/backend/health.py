from django.http import JsonResponse
from django.db import connection
from django_redis import get_redis_connection
from django.core.cache import cache
from django.conf import settings

import requests

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


def get_betterstack_status():
    """
    Получает статусы мониторов Better Stack и кэширует ответ на 2 часа.
    Возвращает список словарей: [{'name': 'front|bots|db', 'status': 'up'|'down', 'uptime': '...'}, ...]
    """
    cache_key = "betterstack_status_cache"
    cache_ttl_seconds = 7200

    def _fetch():
        token = getattr(settings, "BETTERSTACK_API_TOKEN", None)
        print(f"DEBUG_TOKEN_PRESENCE: {bool(token)}")
        if not token:
            print("DEBUG_TOKEN_MISSING, returning empty list")
            return []

        url = "https://uptime.betterstack.com/api/v2/monitors"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        payload = None

        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"DEBUG_RESPONSE_STATUS: {response.status_code}")
            response.raise_for_status()
            payload = response.json()
            print(f"DEBUG_PAYLOAD_KEYS: {payload.keys()}")
        except Exception as e:
            print(f"DEBUG_EXCEPTION_IN_FETCH: {e}")
            return []


        # Унифицируем структуру данных Better Stack
        raw_items = []
        if isinstance(payload, dict) and "data" in payload:
            raw_items = payload.get("data") or []
        elif isinstance(payload, dict) and "monitors" in payload:
            raw_items = payload.get("monitors") or []
        elif isinstance(payload, list):
            raw_items = payload

        wanted_names = {"веб-сайт (api)", "автоматизация и боты (redis)", "база данных заказов (sqlite)"}
        normalized_map = {}

        for item in raw_items:
            attrs = item.get("attributes", {}) if isinstance(item, dict) else {}

            name = (
                attrs.get("pronounceable_name")
                if isinstance(attrs, dict)
                else None
            ) or item.get("pronounceable_name")
            if not isinstance(name, str):
                continue

            lower_name = name.strip().lower()
            if lower_name not in wanted_names:
                continue

            # Статус
            status_value = (
                (attrs.get("status") if isinstance(attrs, dict) else None)
                or item.get("status")
            )
            status_str = str(status_value).lower() if status_value is not None else "unknown"
            status_str = "up" if status_str == "up" else ("down" if status_str == "down" else "down")

            # Аптайм (пытаемся найти наиболее подходящее поле)
            uptime_candidates = []
            if isinstance(attrs, dict):
                uptime_candidates = [
                    attrs.get("uptime"),
                    attrs.get("uptime_percentage"),
                    attrs.get("uptime_30d"),
                    attrs.get("uptime_7d"),
                    attrs.get("uptime_month"),
                ]
            else:
                uptime_candidates = [
                    item.get("uptime"),
                    item.get("uptime_percentage"),
                    item.get("uptime_30d"),
                    item.get("uptime_7d"),
                    item.get("uptime_month"),
                ]

            uptime_value = next((u for u in uptime_candidates if u not in (None, "")), None)
            if isinstance(uptime_value, (int, float)):
                uptime_str = f"{uptime_value:.2f}%"
            else:
                uptime_str = str(uptime_value) if uptime_value else "-"

            normalized_map[lower_name] = {
                "name": lower_name,
                "status": status_str,
                "uptime": uptime_str,
            }

        ordered = []
        for key in ("front", "bots", "db"):
            if key in normalized_map:
                ordered.append(normalized_map[key])

        print(f"DEBUG_RETURNED_MONITORS_COUNT: {len(ordered)}")

        return ordered

    return cache.get_or_set(cache_key, _fetch, cache_ttl_seconds)