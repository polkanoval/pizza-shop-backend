import time
import random
from decimal import Decimal
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction

# Импортируем вспомогательные модели
from .models import OrderItem, STATUS_CHOICES
from menu.models import MenuItem
from .services import calculate_order_totals

@shared_task
def generate_fake_order():
    """
    Задача для автоматической генерации тестового заказа (раз в 4 часа).
    """
    from .models import Order # Локальный импорт против Circular Import

    usernames = ['+79111111111', '+79222222222', '+79333333333']
    User = get_user_model()

    # 1) Выбор пользователя
    user = User.objects.filter(username__in=usernames).order_by('?').first()
    if not user:
        user = User.objects.order_by('?').first()
    if not user:
        raise ValueError("Не найден ни один пользователь для создания заказа.")

    # 2) Выбор 1-2 случайных позиций меню
    all_ids = list(MenuItem.objects.values_list('id', flat=True))
    if not all_ids:
        raise ValueError("Нет доступных MenuItem для создания заказа.")

    k = min(random.choice([1, 2]), len(all_ids))
    chosen_ids = random.sample(all_ids, k=k)
    items_data = [{'pizza': pid, 'quantity': 1} for pid in chosen_ids]

    # 3) Расчет данных через сервис
    calculation_results = calculate_order_totals(user, items_data)

    customer_name_from_profile = (
        getattr(user, 'first_name', None) or
        getattr(user, 'full_name', None) or
        user.username
    )

    # 4) Создание заказа и позиций в атомарной транзакции
    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            customer_name=customer_name_from_profile,
            address='Автогенерация',
            total_price=calculation_results['final_price'],
            discount_amount=calculation_results['discount_amount'],
            applied_discount=calculation_results['applied_discount'],
        )

        for item in items_data:
            OrderItem.objects.create(
                order=order,
                pizza_id=item['pizza'],
                quantity=item['quantity'],
                cost=calculation_results['menu_items_map'][item['pizza']],
            )

        # Если положен подарок
        if calculation_results['final_gift_item_id']:
            OrderItem.objects.create(
                order=order,
                pizza_id=calculation_results['final_gift_item_id'],
                quantity=1,
                cost=Decimal('0.00'),
            )

    print(f"--- СИМУЛЯЦИЯ: Бот создал заказ {order.order_number} для пользователя {user.username} ---")
    return {'order_id': order.id, 'order_number': order.order_number}


@shared_task
def change_order_status(order_id, new_status):
    """
    Задача для автоматической смены статуса заказа.
    Использует time.sleep для обхода проблем с рассинхроном времени в Docker.
    """
    from .models import Order # Локальный импорт против Circular Import

    # ЭТАП 4: Реалистичные задержки
    if new_status == 'preparing':
        print(f"--- CELERY: Заказ #{order_id} поступил. Ждем 5 минут для начала готовки... ---")
        time.sleep(300) # 5 минут
    elif new_status == 'completed':
        print(f"--- CELERY: Заказ #{order_id} готовится. Ждем 10 минут до завершения... ---")
        time.sleep(600) # 10 минут

    print(f"--- CELERY: Начинаю смену статуса заказа #{order_id} на '{new_status}' ---")

    valid_statuses = {choice for choice, _ in STATUS_CHOICES}
    if new_status not in valid_statuses:
        print(f"--- CELERY ОШИБКА: Некорректный статус '{new_status}' ---")
        return f"Invalid status: {new_status}"

    try:
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save(update_fields=['status'])

        print(f"--- CELERY УСПЕХ: Заказ #{order_id} переведен в статус '{new_status}' ---")
        return {'order_id': order_id, 'new_status': new_status, 'updated': True}

    except Order.DoesNotExist:
        print(f"--- CELERY ВНИМАНИЕ: Заказ #{order_id} не найден ---")
        return {'order_id': order_id, 'updated': False}
    except Exception as e:
        print(f"--- CELERY КРИТИЧЕСКАЯ ОШИБКА: {str(e)} ---")
        raise e