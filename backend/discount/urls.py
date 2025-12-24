from rest_framework.routers import DefaultRouter
from .views import DiscountItemViewSet
app_name = 'discount'
router = DefaultRouter()
router.register(r'discount', DiscountItemViewSet)

urlpatterns = router.urls