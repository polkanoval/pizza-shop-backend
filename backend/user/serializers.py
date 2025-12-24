from rest_framework import serializers
from django.contrib.auth.models import User

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name')
        extra_kwargs = {
            'first_name': {'required': True},
        }

    def create(self, validated_data):
       user = User.objects.create_user(**validated_data)
       return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'date_joined')
        read_only_fields = ('username',  'date_joined')

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'password')
        extra_kwargs = {
            'first_name': {'required': False},
        }

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()
        return instance