from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from backend.admin_base import ReadOnlyAdminMixin

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(ReadOnlyAdminMixin, UserAdmin):
    list_display = (
        'username',
        'first_name',
        'date_joined',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.username == 'guest':
            return qs.exclude(username='admin')

        return qs
