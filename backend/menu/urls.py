from rest_framework.routers import DefaultRouter
from .views import MenuItemViewSet
app_name = 'menu'
router = DefaultRouter()
router.register(r'menu', MenuItemViewSet)

urlpatterns = router.urls