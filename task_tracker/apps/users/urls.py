from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationViewSet,
    UserProfileViewSet,
    UserListViewSet
)

router = DefaultRouter()
router.register(r'register', UserRegistrationViewSet, basename='user-register')
router.register(r'profiles', UserProfileViewSet, basename='user-profile')
router.register(r'', UserListViewSet, basename='user-list')

urlpatterns = router.urls