from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet, UserViewSet
from django.urls import path, include
from .authentication import *

#we needed to create an instance out of DefaultRouter so we can be able to call the register method, cuz methods in python are called as instance methods
#and not class methods
router = DefaultRouter
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'users', UserViewSet, basename='user')

#authentication urls
path('auth/login/', CustomTokenObtainPairView.as_view, name='login'),
path('auth/register/', register, name='register'),
path('auth/logout/', logout, name='logout' ),
path('auth/profile/', view_profile, name='profile'),

#inbuilt token
path('auth/refresh-token/', TokenRefreshView.as_view, name='refreshToken')

urlpatterns = path('', include(router.urls))