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

    user = User.objects.filter(username__in=usernames).order_by('?').first()
    if not user:
        user = User.objects.order_by('?').first()
    if not user:
        raise ValueError("Не найден ни один пользователь.")

    all_ids = list(MenuItem.objects.values_list('id', flat=True))
    if not all_ids:
        raise ValueError("Нет доступных MenuItem.")

    k = min(random.choice([1, 2]), len(all_ids))
    chosen_ids = random.sample(all_ids, k=k)
    items_data = [{'pizza': pid, 'quantity': 1} for pid in chosen_ids]

    calculation_results = calculate_order_totals(user, items_data)

    customer_name_from_profile = getattr(user, 'first_name', None) or getattr(user, 'full_name', None) or user.username

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

        if calculation_results['final_gift_item_id']:
            OrderItem.objects.create(
                order=order,
                pizza_id=calculation_results['final_gift_item_id'],
                quantity=1,
                cost=Decimal('0.00'),
            )


    print(f"--- СИМУЛЯЦИЯ: Бот создал заказ {order.order_number} ---")
    return {'order_id': order.id, 'order_number': order.order_number}

@shared_task
def change_order_status(order_id, new_status):
    print(f"--- CELERY: Начинаю смену статуса заказа #{order_id} на '{new_status}' ---")

    try:
        # Используем update_fields для надежности
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save(update_fields=['status'])
        print(f"--- CELERY УСПЕХ: Заказ #{order_id} переведен в '{new_status}' ---")
        return True
    except Order.DoesNotExist:
        print(f"--- CELERY ОШИБКА: Заказ #{order_id} не найден ---")
        return False