from rest_framework import serializers
from .models import DiscountItem

class DiscountItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountItem
        fields = ['id', 'name', 'text', 'image', 'is_available']