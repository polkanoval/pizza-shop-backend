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
                amount = total_price * (discount.discount_value / 100)

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