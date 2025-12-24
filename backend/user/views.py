from rest_framework import generics, status,permissions
from rest_framework.response import Response
from .serializers import RegistrationSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .serializers import UserProfileSerializer
from .serializers import UserProfileUpdateSerializer
from django.contrib.auth import login
from django.shortcuts import redirect

class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"message": "Профиль успешно обновлен"}, status=status.HTTP_200_OK)

def guest_admin_login(request):
    # Получаем или создаем пользователя-гостя
    guest_user, created = User.objects.get_or_create(
        username='guest',
        defaults={
            'is_staff': True,  # Доступ в админку
            'is_active': True
        }
    )

    # Принудительно логиним (без проверки пароля)
    login(request, guest_user, backend='django.contrib.auth.backends.ModelBackend')

    # Перенаправляем в корень админки
    return redirect('admin:index')