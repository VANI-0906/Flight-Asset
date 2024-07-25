from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

 
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
 
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        if User.objects.filter(username=username).exists():
            return Response({"detail": "User already exists."}, status=status.HTTP_400_BAD_REQUEST)
       
        response = super().create(request, *args, **kwargs)
       
        response_data = {
            "message": "User created successfully",
            "user": response.data
        }
       
        return Response(response_data, status=status.HTTP_201_CREATED)
    
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
 
        user = authenticate(username=username, password=password)
 
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
 
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh_token': str(refresh),
            'refresh_token_validlity': "(valid for 1 day)",
            'access_token': str(refresh.access_token),
            'access_token_validity': "(valid for 10 minutes)"
        })


class RefreshTheAccessToken(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

            return Response({
                'access_token': new_access_token,
                'access_token_validity': "(valid for 10 minutes)"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)







