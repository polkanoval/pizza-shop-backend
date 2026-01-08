from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Order, OrderItem


def get_dashboard_stats():
    """
    Возвращает статистику для дашборда.
    - orders_count: количество заказов за сегодня
    - total_revenue: сумма total_price всех заказов за сегодня
    - labels_revenue: список дат за последние 7 дней (строки "дд.мм")
    - data_revenue: список сумм выручки за эти 7 дней
    - labels_pizza: названия топ-5 популярных пицц
    - data_pizza: количество их продаж
    """
    now = timezone.now()
    today = now.date()

    # Заказы за сегодня
    orders_today_qs = Order.objects.filter(created_at__date=today)
    orders_count = orders_today_qs.aggregate(count=Count("id"))["count"] or 0
    total_revenue = (
        orders_today_qs.aggregate(total=Sum("total_price"))["total"] or Decimal("0")
    )

    start_of_week = today - timedelta(days=6)
    start_of_month = today - timedelta(days=30)

    # Статистика за последнюю неделю (7 дней)
    orders_week_qs = Order.objects.filter(created_at__date__gte=start_of_week, created_at__date__lte=today)
    orders_week_count = orders_week_qs.aggregate(count=Count("id"))["count"] or 0
    revenue_week = orders_week_qs.aggregate(total=Sum("final_price"))["total"] or Decimal("0")

    # Статистика за последний месяц (30 дней)
    orders_month_qs = Order.objects.filter(created_at__date__gte=start_of_month, created_at__date__lte=today)
    orders_month_count = orders_month_qs.aggregate(count=Count("id"))["count"] or 0
    revenue_month = orders_month_qs.aggregate(total=Sum("final_price"))["total"] or Decimal("0")


    # Выручка за последние 7 дней (включая сегодня) для графика
    start_date = today - timedelta(days=6)

    revenue_qs = (
        Order.objects.filter(created_at__date__gte=start_date, created_at__date__lte=today)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("final_price"))
    )
    revenue_by_day = {row["day"]: row["revenue"] or Decimal("0") for row in revenue_qs}

    days_window = [start_date + timedelta(days=i) for i in range(7)]
    labels_revenue = [d.strftime("%d.%m") for d in days_window]
    data_revenue = [revenue_by_day.get(d, Decimal("0")) for d in days_window]

    # Топ-5 популярных пицц по количеству продаж (по сумме quantity)
    top_pizzas_qs = (
        OrderItem.objects.values("pizza__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )
    labels_pizza = [row["pizza__name"] for row in top_pizzas_qs]
    data_pizza = [row["total_sold"] or 0 for row in top_pizzas_qs]

    # NB: Добавляем выборку последних 5 заказов для отображения в админке
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]


    return {
        "orders_count": orders_count, # Заказы сегодня
        "total_revenue": total_revenue, # Выручка сегодня

        # Новые метрики
        "orders_week_count": orders_week_count,
        "revenue_week": revenue_week,
        "orders_month_count": orders_month_count,
        "revenue_month": revenue_month,

        "labels_revenue": labels_revenue,
        "data_revenue": data_revenue,
        "labels_pizza": labels_pizza,
        "data_pizza": data_pizza,

        # NB: Вот новый ключ, который вам нужен в шаблоне
        "recent_orders": recent_orders,
    }

# --- Вторая часть файла: calculate_order_totals ---

from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import Order, DiscountItem, MenuItem

User = get_user_model()

def calculate_order_totals(user, items_data):
    if not items_data:
        raise ValueError("Order must contain items.")
    # Получаю актуальные цены из базы данных
    menu_item_ids = [item.get('pizza') for item in items_data]
    menu_items = MenuItem.objects.filter(id__in=menu_item_ids)
    # Создаю словарь ID -> Цена для быстрого доступа
    menu_items_map = {item.id: item.cost for item in menu_items}

    total_base_price = Decimal('0.00')
    total_items_count = 0
    item_prices_in_order = []

    for item_data in items_data:
        pizza_id = item_data.get('pizza')
        quantity = item_data.get('quantity')
        if pizza_id not in menu_items_map:
            raise MenuItem.DoesNotExist(f"Menu item {pizza_id} not found.")

        actual_cost = menu_items_map[pizza_id]
        total_base_price += actual_cost * quantity
        total_items_count += quantity
        item_prices_in_order.append((actual_cost, pizza_id))

    total_price = total_base_price

    potential_discounts = []
    if user and user.is_authenticated:
        available_discounts = DiscountItem.objects.filter(is_available=True)

        for discount in available_discounts:
            is_applicable = True

            # 1. Проверка на первый заказ
            if discount.is_first_order_only:
                if user is None or not user.is_authenticated:
                    is_applicable = False
                elif Order.objects.filter(user=user).exists():
                    is_applicable = False

            # 2. Проверка условия "N товаров в заказе"
            min_qty_required = int(discount.min_item_qty) if discount.min_item_qty is not None else 0

            if min_qty_required > 0:
                if total_items_count < min_qty_required:
                    is_applicable = False

            # Если хотя бы одно условие не выполнено, пропускаем эту скидку
            if not is_applicable:
                continue

            # Расчет всех варинтов применимых скидок
            amount = Decimal('0.00')
            gift_item_id = None

            if discount.discount_type == 'PERCENT' and discount.discount_value is not None:
                # NB: Исправлено использование Decimal для точности
                amount = total_price * (Decimal(str(discount.discount_value)) / Decimal('100'))

            elif discount.discount_type == 'GIFT_ITEM':
                if discount.every_n_item_free is not None and discount.every_n_item_free > 0:
                    n = int(discount.every_n_item_free)
                    gifts_count = total_items_count // n

                    if gifts_count > 0:
                        if not item_prices_in_order:
                            continue

                        # Находим самый дешевый товар
                        cheapest_item_price, cheapest_item_id_val = sorted(item_prices_in_order, key=lambda x: x[0])[0]
                        amount = cheapest_item_price * gifts_count
                        gift_item_id = cheapest_item_id_val

            if amount > 0:
                 potential_discounts.append({
                     'amount': amount,
                     'discount_item': discount,
                     'gift_item_id': gift_item_id
                })

    # Делаю выбор скидки, беру самую выгодную, которая применится
    applied_discount = None
    final_gift_item_id = None
    discount_to_save_in_db = Decimal('0.00')

    if potential_discounts:
        best_offer = sorted(potential_discounts, key=lambda x: x['amount'], reverse=True)[0]
        applied_discount = best_offer['discount_item']
        discount_to_save_in_db = best_offer['amount']
        final_gift_item_id = best_offer['gift_item_id']

    final_price = total_price - discount_to_save_in_db

    return {
        'total_price_before_discount': total_price,
        'discount_amount': discount_to_save_in_db,
        'final_price': final_price,
        'applied_discount': applied_discount,
        'final_gift_item_id': final_gift_item_id,
        'menu_items_map': menu_items_map,
    }