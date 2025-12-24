from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DiscountItem
from backend.admin_base import ReadOnlyAdminMixin

@admin.register(DiscountItem)
class DiscountItemAdmin(ReadOnlyAdminMixin,admin.ModelAdmin):
    list_display = ('name', 'text', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name',)