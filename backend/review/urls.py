from django.urls import path
from .views import ReviewListCreateView, ReviewDeleteView

urlpatterns = [
    path('', ReviewListCreateView.as_view(), name='review-list-create'),
    path('<int:pk>/delete/', ReviewDeleteView.as_view(), name='review-delete'),
]