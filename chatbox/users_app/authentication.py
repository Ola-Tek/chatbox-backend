from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from django.db.models import Q 
from .serializers import ConversationSerializer, UserSerializer, UserProfileSerializer
from .models import *
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom Login View
    it inherits from an inbuilt method called TokenObtainPairView which has a method
    called post that helps log in the user and also create access and refresh token"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get('email')
            
            try:
                user = User.objects.get(email=email)
                user.is_online = True
                user.save()
            except User.DoesNotExist:
                    raise Exception("User does not exist!")
        return response
    
@api_view(['POST'])
@permission_classes(['AllowAny'])
def register(request):
    """it points the user to the registratiion view"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid:
        user = serializer.save()
        user.set_password(request.data.get('password'))
        user.save()
        #generate refresh token for immediate logins
        refresh = RefreshToken.for_user(user)
        return Response({
            'Message' : 'User has registered Successfully',
            'user' : UserSerializer(user).data,
            'refresh' : str(refresh),
            'access' : str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view({'POST'})
def logout(request):
    """ viewset to logout """
    try:
        refresh_token = UserSerializer(request.data.get('refresh_token')) #since we want to log out, we have to get the refresh token to blacklist it
        token = RefreshToken(refresh_token) #we have to instantiate it using the RefreshToken, so we can easily use the method 'blacklist'
        token.blacklist()
        
        #then we switch online to be false, so we won't be able to see them online
        request.user.is_online = False
        request.user.save()
        
        return Response({'message': "User logged out successfully"}, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        print(f"Token Error: {e}") #this prints the original error caught by e and print it on the terminal
        return Response({"error": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view({'GET'})
def view_profile(request):
    "the view function that shows, get the current user profile"
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)
    
        
    