from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from .services import calculate_order_totals
from .models import Order, OrderItem, MenuItem
from .serializers import OrderSerializer

User = get_user_model()

# список заказов пользователя
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Order.objects
            .filter(user=user)
            .select_related('user', 'applied_discount')
            .prefetch_related('items__pizza')
            .order_by('-created_at')
        )

# создание заказа
class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user
        items_data = self.request.data.get('items', [])

        try:
            calculation_results = calculate_order_totals(user, items_data)
        except (MenuItem.DoesNotExist, ValueError) as e:
             raise ValidationError({"detail": str(e)})

        discount_to_save_in_db = calculation_results['discount_amount']
        applied_discount_instance = calculation_results['applied_discount']
        final_gift_item_id = calculation_results['final_gift_item_id']
        menu_items_map = calculation_results['menu_items_map']
        # Важно: берем цену ДО скидки для корректного сохранения в модель
        total_before_discount = calculation_results['total_price_before_discount']

        # Чтобы целостно работать с бд
        with transaction.atomic():
            # NB: Исправлено! Передаем базовую цену.
            # Модель сама сделает: final_price = total_price - discount_amount
            order_instance = serializer.save(
                user=user,
                total_price=total_before_discount,
                discount_amount=discount_to_save_in_db,
                applied_discount=applied_discount_instance
            )

            # Создаем позиции заказа с ценами из меню на момент покупки
            for item_data in items_data:
                OrderItem.objects.create(
                    order=order_instance,
                    pizza_id=item_data['pizza'],
                    quantity=item_data['quantity'],
                    cost=menu_items_map[item_data['pizza']]
                )

            # Если расчет выявил подарок (GIFT_ITEM), добавляем его как позицию с 0 ценой
            if final_gift_item_id:
                OrderItem.objects.create(
                    order=order_instance,
                    pizza_id=final_gift_item_id,
                    quantity=1,
                    cost=Decimal('0.00')
                )

# для отображения рассчитанной стоимости и скидок на frontend
class CartTotalPreviewView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        user = request.user
        items_data = request.data.get('items', [])

        try:
            calculation_results = calculate_order_totals(user, items_data)
        except (MenuItem.DoesNotExist, ValueError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Подготовка данных для фронтенда
        applied_discount = calculation_results['applied_discount']
        applied_discount_name = getattr(applied_discount, 'name', None)
        applied_discount_type = getattr(applied_discount, 'discount_type', None)
        gift_item_id = calculation_results['final_gift_item_id']

        return Response({
            # 1. Расчет полной стоимости (без скидок)
            'total_price_before_discount': calculation_results['total_price_before_discount'],

            # 2. Информация о скидке
            'discount_amount': calculation_results['discount_amount'],
            'applied_discount_name': applied_discount_name,
            'applied_discount_type': applied_discount_type,
            'gift_item_id': gift_item_id,

            # 3. Результат после вычитания (то, что увидит пользователь на экране)
            'final_price': calculation_results['final_price'],
        })