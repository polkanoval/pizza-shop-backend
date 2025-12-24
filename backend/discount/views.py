from django.shortcuts import render

from rest_framework import viewsets
from .models import DiscountItem
from .serializers import DiscountItemSerializer

class DiscountItemViewSet(viewsets.ModelViewSet):
    queryset = DiscountItem.objects.all().filter(is_available=True)
    serializer_class = DiscountItemSerializer
