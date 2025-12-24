from django.contrib import admin
from .models import Order
from backend.admin_base import ReadOnlyAdminMixin

@admin.register(Order)
class OrderAdmin(ReadOnlyAdminMixin,admin.ModelAdmin):
    list_display = (
        'id',
        'get_username',
        'customer_name',
        'address',
        'total_price',
        'status',
        'created_at'
    )
    list_filter = ('status','created_at',)
    list_editable = ('status',)
    search_fields = ('customer_name', 'address', 'id')
    def get_username(self, obj):
           if obj.user:
               return obj.user.username
           return "Не зарегистрирован"

    get_username.short_description = 'Телефон пользователя'

    get_username.admin_order_field = 'user__username'