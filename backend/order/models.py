from django.db import models, transaction
from menu.models import MenuItem
from discount.models import DiscountItem
from django.contrib.auth.models import User

STATUS_CHOICES = (
    ('accepted', 'accepted'),
    ('preparing', 'preparing'),
    ('completed', 'completed'),
)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    final_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    applied_discount = models.ForeignKey(DiscountItem, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')
    created_at = models.DateTimeField(auto_now_add=True)
    order_number = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def __str__(self):
        return f"Order {self.order_number} by {self.customer_name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.final_price = self.total_price - self.discount_amount

        if not self.order_number and self.user and self.user.username:
            base_phone = self.user.username
            if base_phone.startswith('+7'):
                base_phone = base_phone[2:]
            # Считаем количество существующих заказов для этого пользователя
            count = Order.objects.filter(user=self.user).count() + 1
            self.order_number = f"{base_phone}-{count}"

        super().save(*args, **kwargs)

        # Если это новый заказ, отправляем задачи в воркер
        if is_new:
            def _enqueue():
                from .tasks import change_order_status
                # Мы используем .delay(), так как задержка (5 и 10 мин)
                # теперь реализована через time.sleep внутри таски
                change_order_status.delay(self.id, 'preparing')
                change_order_status.delay(self.id, 'completed')

            transaction.on_commit(_enqueue)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    pizza = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    cost = models.DecimalField(max_digits=5, decimal_places=0)

    def __str__(self):
        return f"{self.quantity} x {self.pizza.name} in Order {self.order.order_number}"