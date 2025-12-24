from django.shortcuts import render

from rest_framework import viewsets
from .models import MenuItem
from .serializers import MenuItemSerializer

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all().filter(is_available=True)
    serializer_class = MenuItemSerializer
