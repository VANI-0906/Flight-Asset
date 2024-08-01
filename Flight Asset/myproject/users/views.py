from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenRefreshView

 
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
        
        


# views.py
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import FlightQuerySerializer, FlightResponseSerializer
 
class FlightDetailsView(APIView):
    def post(self, request):
        # Deserialize the request data
        serializer = FlightQuerySerializer(data=request.data)
       
        if not serializer.is_valid():
            return Response({'error': 'Invalid input', 'details': serializer.errors}, status=400)
       
        # Get validated data
        validated_data = serializer.validated_data
        place = validated_data.get('place')
        date = validated_data.get('date', '2024-08-10')  # Use default date if not provided
 
        # Obtain an access token from Amadeus
        token_url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
        token_payload = {
            'grant_type': 'client_credentials',
            'client_id': settings.AMADEUS_API_KEY,
            'client_secret': settings.AMADEUS_API_SECRET
        }
 
        token_response = requests.post(token_url, data=token_payload)
       
        if token_response.status_code != 200:
            return Response({
                'error': 'Failed to generate access token',
                'details': token_response.json()
            }, status=500)
 
        access_token = token_response.json().get('access_token')
 
        # Initialize counters
        place_counts = {'outgoing': 0, 'incoming': 0}
 
        # Define flight search parameters
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        flight_offers_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
 
        # Handle scenarios based on provided input
        if place:
            # If place is provided
            search_params_departures = {
                'originLocationCode': place,
                'destinationLocationCode': 'LAX',  # Example destination; adjust as needed
                'departureDate': date,
                'adults': 1,
                'currencyCode': 'USD'
            }
 
            flight_response_departures = requests.get(flight_offers_url, headers=headers, params=search_params_departures)
 
            if flight_response_departures.status_code == 200:
                flight_data_departures = flight_response_departures.json()
                place_counts['outgoing'] = sum(
                    1 for offer in flight_data_departures.get('data', [])
                    for itinerary in offer.get('itineraries', [])
                    for segment in itinerary.get('segments', [])
                    if segment['departure']['iataCode'] == place
                )
            else:
                return Response({
                    'error': 'Failed to fetch outgoing flight details',
                    'details': flight_response_departures.json()
                }, status=500)
 
            search_params_arrivals = {
                'originLocationCode': 'LAX',  # Example origin; adjust as needed
                'destinationLocationCode': place,
                'departureDate': date,
                'adults': 1,
                'currencyCode': 'USD'
            }
 
            flight_response_arrivals = requests.get(flight_offers_url, headers=headers, params=search_params_arrivals)
 
            if flight_response_arrivals.status_code == 200:
                flight_data_arrivals = flight_response_arrivals.json()
                place_counts['incoming'] = sum(
                    1 for offer in flight_data_arrivals.get('data', [])
                    for itinerary in offer.get('itineraries', [])
                    for segment in itinerary.get('segments', [])
                    if segment['arrival']['iataCode'] == place
                )
            else:
                return Response({
                    'error': 'Failed to fetch incoming flight details',
                    'details': flight_response_arrivals.json()
                }, status=500)
 
        elif date:
            # If only date is provided
            search_params = {
                'originLocationCode': 'JFK',  # Default origin; adjust as needed
                'destinationLocationCode': 'LAX',  # Default destination; adjust as needed
                'departureDate': date,
                'returnDate': date,
                'adults': 1,
                'currencyCode': 'USD'
            }
 
            flight_response = requests.get(flight_offers_url, headers=headers, params=search_params)
 
            if flight_response.status_code == 200:
                flight_data = flight_response.json()
                # Adjust the counts based on the response data
                place_counts['outgoing'] = len(flight_data.get('data', []))
                place_counts['incoming'] = len(flight_data.get('data', []))
            else:
                return Response({
                    'error': 'Failed to fetch flight details',
                    'details': flight_response.json()
                }, status=500)
 
        else:
            return Response({'error': 'Place or date parameter is required'}, status=400)
 
        # Create the final response data
        response_data = {
            'place': place if place else 'All places',
            'numberOfDepartures': place_counts['outgoing'],
            'numberOfArrivals': place_counts['incoming']
        }
 
        # Serialize the response data
        response_serializer = FlightResponseSerializer(data=response_data)
       
        if not response_serializer.is_valid():
            return Response({'error': 'Failed to serialize response data', 'details': response_serializer.errors}, status=500)
 
        # Return the filtered response
        return Response(response_serializer.data)




