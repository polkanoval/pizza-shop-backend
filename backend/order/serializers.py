from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    pizza_name = serializers.ReadOnlyField(source='pizza.name')
    price = serializers.DecimalField(source='cost', max_digits=5, decimal_places=0, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['pizza', 'pizza_name', 'quantity', 'cost', 'price']
        read_only_fields = ['cost', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)


    class Meta:
        model = Order
        fields = ['id', 'username', 'customer_name', 'address', 'total_price', 'discount_amount','final_price','applied_discount', 'status', 'created_at', 'items', 'order_number']
        read_only_fields = ['user', 'created_at', 'discount_amount', 'final_price', 'applied_discount', 'total_price', 'order_number']