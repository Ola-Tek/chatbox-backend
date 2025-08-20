from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'room', ChatRoomViewSet, basename='chatroom')
router.register(r'online-user', OnlineUserViewSet, basename='online_user')
router.register(r'typing', TypingIndicatorViewSet, basename='typing_indicator')
router.register(r'delivery-status', MessageDeliveryStatusViewSet, basename='message_delivery_status')

urlpatterns = [
    path('', include(router.urls)),
]
