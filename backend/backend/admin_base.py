from django.contrib import admin

class ReadOnlyAdminMixin:
    """Миксин, запрещающий любые изменения для пользователя guest"""

    def has_view_permission(self, request, obj=None):
        return True # Разрешаем смотреть всем

    def has_add_permission(self, request):
        if request.user.username == 'guest':
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.username == 'guest':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'guest':
            return False
        return super().has_delete_permission(request, obj)