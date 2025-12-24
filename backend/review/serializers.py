from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_first_name = serializers.CharField(source='author.first_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'author_username', 'author_first_name','evaluation', 'feedback', 'date_created', 'author', 'is_published']
        read_only_fields = ['author', 'is_published']