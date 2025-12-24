from django.urls import path
from .views import OrderCreateView, CartTotalPreviewView, OrderListView

app_name = 'order'

urlpatterns = [
    path('order/preview_total/', CartTotalPreviewView.as_view(), name='cart-total-preview'),
    path('order/', OrderCreateView.as_view(), name='order-create'),
    path('orders/', OrderListView.as_view(), name='order-list'),
]