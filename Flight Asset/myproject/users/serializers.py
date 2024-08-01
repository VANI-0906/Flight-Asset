from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
 
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
 
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'confirm_password')
 
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if len(attrs['password']) >= 8:
            raise serializers.ValidationError({"password": "Password must be less than 8 characters."})
        return attrs
 
    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    

 
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},  # Ensure password is write-only
        }
 
class LoginSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
 
    def to_representation(self, instance):
        data = super().to_representation(instance)
        refresh_token = RefreshToken(instance['refresh'])
        data['refresh'] = {
            'token': data['refresh'],
            'expires_in': str(refresh_token.access_token_lifetime),
        }
        data['access'] = {
            'token': data['access'],
            'expires_in': str(refresh_token.refresh_token_lifetime),
        }
        return data



class FlightQuerySerializer(serializers.Serializer):
    place = serializers.CharField(required=False)
    date = serializers.DateField(required=False)
 
class FlightResponseSerializer(serializers.Serializer):
    place = serializers.CharField()
    numberOfDepartures = serializers.IntegerField()
    numberOfArrivals = serializers.IntegerField()