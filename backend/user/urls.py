from django.urls import path
from .views import RegistrationView,UserProfileView
from .views import ProfileUpdateView


urlpatterns = [
    path('register/', RegistrationView.as_view(), name='user_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
]