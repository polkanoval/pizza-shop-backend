from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import random

from .models import Order, OrderItem, STATUS_CHOICES
from menu.models import MenuItem
from .services import calculate_order_totals


@shared_task
def generate_fake_order():
    usernames = ['+79111111111', '+79222222222', '+79333333333']
    User = get_user_model()

    # 1) Выбор пользователя
    user = User.objects.filter(username__in=usernames).order_by('?').first()
    if not user:
        # Фолбэк на любого пользователя, если из списка никого нет
        user = User.objects.order_by('?').first()
    if not user:
        raise ValueError("Не найден ни один пользователь для создания тестового заказа.")

    # 2) Выбор 1-2 случайных позиций меню
    all_ids = list(MenuItem.objects.values_list('id', flat=True))
    if not all_ids:
        raise ValueError("Нет доступных MenuItem для создания заказа.")
    k = min(random.choice([1, 2]), len(all_ids))
    chosen_ids = random.sample(all_ids, k=k)

    items_data = [{'pizza': pid, 'quantity': 1} for pid in chosen_ids]

    # 3) Расчет данных через сервис
    calculation_results = calculate_order_totals(user, items_data)
    discount_to_save_in_db = calculation_results['discount_amount']
    applied_discount_instance = calculation_results['applied_discount']
    final_gift_item_id = calculation_results['final_gift_item_id']
    menu_items_map = calculation_results['menu_items_map']
    final_price = calculation_results['final_price']

    # 4) Создание заказа и позиций
    with transaction.atomic():
        order = Order.objects.create(
            user=user,
            customer_name=getattr(user, 'username', 'Автогенерация'),
            address='Автогенерация',
            # Следуем текущей логике проекта (как в OrderCreateView):
            total_price=final_price,
            discount_amount=discount_to_save_in_db,
            applied_discount=applied_discount_instance,
        )

        for item in items_data:
            OrderItem.objects.create(
                order=order,
                pizza_id=item['pizza'],
                quantity=item['quantity'],
                cost=menu_items_map[item['pizza']],
            )

        if final_gift_item_id:
            OrderItem.objects.create(
                order=order,
                pizza_id=final_gift_item_id,
                quantity=1,
                cost=Decimal('0.00'),
            )

    # 5) Отчетность в логи
    print(f"--- СИМУЛЯЦИЯ: Бот создал заказ {order.order_number} для пользователя {user.username} ---")
    return {'order_id': order.id, 'order_number': order.order_number}


@shared_task
def change_order_status(order_id, new_status):
    """
    Задача для автоматической смены статуса заказа.
    """
    print(f"--- CELERY: Начинаю смену статуса заказа #{order_id} на '{new_status}' ---")

    valid_statuses = {choice for choice, _ in STATUS_CHOICES}
    if new_status not in valid_statuses:
        print(f"--- CELERY ОШИБКА: Некорректный статус '{new_status}' ---")
        return f"Invalid status: {new_status}"

    try:
        # Используем .update(), чтобы избежать конфликтов блокировки всей таблицы
        updated = Order.objects.filter(id=order_id).update(status=new_status)

        if updated:
            print(f"--- CELERY УСПЕХ: Заказ #{order_id} переведен в статус '{new_status}' ---")
        else:
            print(f"--- CELERY ВНИМАНИЕ: Заказ #{order_id} не найден ---")

        return {'order_id': order_id, 'new_status': new_status, 'updated': bool(updated)}

    except Exception as e:
        print(f"--- CELERY КРИТИЧЕСКАЯ ОШИБКА: {str(e)} ---")
        raise e