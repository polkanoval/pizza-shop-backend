from django.contrib import admin

from .models import MenuItem
from backend.admin_base import ReadOnlyAdminMixin

@admin.register(MenuItem)
class MenuItemAdmin(ReadOnlyAdminMixin,admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'cost', 'image')
        }),
        ('Availability', {
            'fields': ('is_available',),
            'classes': ('collapse',), # Скрывает этот раздел по умолчанию
        }),
    )
    list_display = ('name', 'cost', 'is_available',  'description')
    list_filter = ('is_available',)
    search_fields = ('name',)