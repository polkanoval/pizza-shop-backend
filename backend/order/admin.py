from django.contrib import admin
from .models import Order
from backend.admin_base import ReadOnlyAdminMixin
from .services import get_dashboard_stats

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

# Сохраняем оригинальный индекс админки
_original_admin_index = admin.site.index

def new_index(request, extra_context=None):
    stats = get_dashboard_stats()
    if extra_context is None:
        extra_context = {}
    else:
        # копия чтобы не мутировать исходный словарь
        extra_context = dict(extra_context)
    extra_context.update(stats)
    return _original_admin_index(request, extra_context=extra_context)

# Назначаем новый индекс и шаблон
admin.site.index = new_index
admin.site.index_template = "admin/dashboard.html"