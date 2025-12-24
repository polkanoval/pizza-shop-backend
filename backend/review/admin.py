from django.contrib import admin

from .models import Review
from backend.admin_base import ReadOnlyAdminMixin

@admin.register(Review)
class ReviewAdmin(ReadOnlyAdminMixin,admin.ModelAdmin):
    list_display  = ('author', 'evaluation', 'feedback','date_created','is_published')
    list_filter   = ('is_published','date_created',)
    list_editable = (
        'is_published',
    )
    search_fields = ('author',)