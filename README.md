Pizza Shop Backend

### Описание
Backend для пиццерии на Django + DRF: меню, скидки, заказы, отзывы и профиль пользователя. JWT-аутентификация, Celery-задачи, Redis-кэш.


### Стек
- Язык: Python 3.12
- Фреймворк: Django 5.2 + Django REST Framework
- Аутентификация: JWT (djangorestframework-simplejwt)
- БД: SQLite (по умолчанию). Опционально PostgreSQL
- ORM: Django ORM
- Кэш/брокер: Redis (django-redis), Celery для фоновых задач
- UI админки: Jazzmin


### Структура API (основные эндпоинты)
Базовый префикс для API: `/api/`

- Health
  - GET `/api/health/db/` — состояние БД
  - GET `/api/health/bots/` — состояние Redis/ботов
  - GET `/api/health/front/` — жив ли процесс Django

- Аутентификация (JWT)
  - POST `/api/token/` — получить пару токенов (access/refresh)
  - POST `/api/token/refresh/` — обновить access-токен

- Меню (`menu`)
  - `/api/menu/` — список/создание
  - `/api/menu/{id}/` — детально/обновление/удаление

- Скидки (`discount`)
  - `/api/discount/` — список/создание
  - `/api/discount/{id}/` — детально/обновление/удаление

- Заказы (`order`)
  - POST `/api/order/preview_total/` — предварительный расчет корзины и скидок
  - POST `/api/order/` — создать заказ (JWT рекомендуется)
  - GET `/api/orders/` — список заказов текущего пользователя (JWT)

- Пользователь (`user`)
  - POST `/api/user/register/` — регистрация
  - GET `/api/user/profile/` — профиль текущего пользователя (JWT)
  - PATCH `/api/user/profile/update/` — частичное обновление профиля (JWT)

- Отзывы (`review`)
  - GET/POST `/api/review/` — список и создание отзывов
  - DELETE `/api/review/{id}/delete/` — удаление отзыва по id

- Админка
  - `/cpanel/` — стандартная админка Django (Jazzmin)
  - `/demo-admin/` — вход гостем в админку (для демо)

Примечание: Доступ на запись на публичных viewset'ах может потребовать донастройки прав (по умолчанию у DRF — AllowAny, в проекте включена JWT-аутентификация). Для продакшена рекомендуется ограничить методы записи админ-пользователями.


### Как запустить локально
1) Перейдите в каталог проекта с `manage.py`:
```
cd backend
```

2) Создайте и активируйте виртуальное окружение:
- Windows (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
- Linux/macOS:
```
python -m venv .venv
source .venv/bin/activate
```

3) Установите зависимости:
```
pip install -r requirements.txt
```

4) (Опционально) Задайте переменные окружения через `.env` (см. ниже), либо установите их напрямую в сессии терминала.

5) Примените миграции и создайте суперпользователя:
```
python manage.py migrate
python manage.py createsuperuser
```

6) Запустите сервер разработки:
```
python manage.py runserver
```
По умолчанию бэкенд будет доступен на `http://127.0.0.1:8000/`. CORS уже разрешает `http://localhost:3000` для фронтенда.


### .env и подключение к БД
Проект читает переменные из окружения (os.environ). Файл `.env` не подхватывается автоматически, его можно экспортировать вручную в текущую сессию (см. ниже).

Минимальный пример `.env` (для разработки на SQLite ничего настраивать не нужно):
```
DJANGO_SECRET_KEY=dev-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
# Опционально:
BETTERSTACK_API_TOKEN=
```
Загрузить `.env` в окружение:
- Windows PowerShell (на время текущей сессии):
```
Get-Content .env | ForEach-Object {
  if ($_ -and $_ -notmatch '^#') {
    $name,$value = $_ -split '=',2
    $env:$name = $value
  }
}
```
- Linux/macOS (bash/zsh):
```
export $(grep -v '^#' .env | xargs)
```


#### SQLite (по умолчанию)
Ничего дополнительно не требуется. Настройка уже в `backend/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {'timeout': 30},
    }
}
```

#### Переключение на PostgreSQL (опционально)
1) Добавьте драйвер в зависимости (если используете Postgres):
```
pip install psycopg2-binary
```

2) Опишите в `.env` параметры подключения:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=pizza
DB_USER=pizza_user
DB_PASSWORD=pizza_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

3) В `backend/settings.py` замените блок `DATABASES` (или оберните в условие) на чтение из окружения с fallback на SQLite, например:
```python
DB_ENGINE = os.environ.get('DB_ENGINE')
if DB_ENGINE:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {'timeout': 30},
        }
    }
```

4) Примените миграции повторно:
```
python manage.py migrate
```

Примечание: Для фоновых задач (Celery) понадобится запущенный Redis. Для базового запуска API Redis не обязателен.


### Полезные пути
- Админка: `/cpanel/`
- JWT: `/api/token/`, `/api/token/refresh/`
- Медиа (dev): `/media/` (раздаются при DEBUG=True)