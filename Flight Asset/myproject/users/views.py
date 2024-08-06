import json
import os
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, FlightQuerySerializer, FlightResponseSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenRefreshView
from datetime import datetime
import requests
from django.conf import settings
from .models import APIUsageLog
 
def log_api_usage(user, endpoint, query_params):
   
    if user and user.is_authenticated:
        APIUsageLog.objects.create(user=user, endpoint=endpoint, query_params=query_params)
 
 
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
        log_api_usage(request.user, request.path, request.data)
        return Response(response_data, status=status.HTTP_201_CREATED)
   
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
 
        user = authenticate(username=username, password=password)
 
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
 
        refresh = RefreshToken.for_user(user)
 
        log_api_usage(request.user, request.path, request.data)
       
        return Response({
            'refresh_token': str(refresh),
            'refresh_token_validity': "valid for 1 day",
            'access_token': str(refresh.access_token),
            'access_token_validity': "valid for 10 minutes"
        })
 
 
class RefreshTheAccessToken(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
 
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
 
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
 
            log_api_usage(request.user, request.path, request.data)
       
            return Response({
                'access_token': new_access_token,
                'access_token_validity': "(valid for 10 minutes)"
            }, status=status.HTTP_200_OK)
 
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
class FlightDetailsView(APIView):
   
    def post(self, request):
        # Deserialize the request data
        serializer = FlightQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Invalid input', 'details': serializer.errors}, status=400)
 
        # Get validated data
        validated_data = serializer.validated_data
        user_access_token = validated_data.get('access_token')
        place = validated_data.get('place')
        date = validated_data.get('date')
 
        # Use the current date if no date is provided
        if not date:
            date = datetime.today().strftime('%Y-%m-%d')
 
 
        # Obtain an access token from Amadeus
        token_url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
        token_payload = {
            'grant_type': 'client_credentials',
            'client_id': settings.AMADEUS_API_KEY,
            'client_secret': settings.AMADEUS_API_SECRET
        }
 
        try:
            token_response = requests.post(token_url, data=token_payload, verify=False)
        except requests.exceptions.SSLError as e:
            return Response({
                'error': 'SSL verification failed',
                'details': str(e)
            }, status=500)
 
        if token_response.status_code != 200:
            return Response({
                'error': 'Failed to generate access token',
                'details': token_response.json()
            }, status=500)
 
        access_token = token_response.json().get('access_token')
 
        # Define flight search parameters
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        flight_offers_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
 
        # List of predefined places in India
        predefined_places = ['BLR', 'DEL', 'MAA', 'BOM', 'HYD', 'CCU']
 
        # If a specific place is provided, restrict to that place, otherwise, use all predefined places
        places_to_process = [place] if place else predefined_places
        response_data = []
 
        # Process each place
        for origin in places_to_process:
            outgoing_count = 0
            incoming_count = 0
 
            for destination in predefined_places:
                if origin == destination:
                    continue  # Skip if origin and destination are the same
 
                # Fetch departure flights
                search_params_departures = {
                    'originLocationCode': origin,
                    'destinationLocationCode': destination,
                    'departureDate': date,
                    'adults': 1,
                    'currencyCode': 'INR'
                }
 
                try:
                    flight_response_departures = requests.get(flight_offers_url, headers=headers, params=search_params_departures, verify=False)
                except requests.exceptions.SSLError as e:
                    return Response({
                        'error': 'SSL verification failed',
                        'details': str(e)
                    }, status=500)
 
                if flight_response_departures.status_code == 200:
                    flight_data_departures = flight_response_departures.json()
                    outgoing_count += sum(
                        1 for offer in flight_data_departures.get('data', [])
                        for itinerary in offer.get('itineraries', [])
                        for segment in itinerary.get('segments', [])
                        if segment['departure']['iataCode'] == origin
                    )
 
                # Fetch arrival flights
                search_params_arrivals = {
                    'originLocationCode': destination,
                    'destinationLocationCode': origin,
                    'departureDate': date,
                    'adults': 1,
                    'currencyCode': 'INR'
                }
 
                try:
                    flight_response_arrivals = requests.get(flight_offers_url, headers=headers, params=search_params_arrivals, verify=False)
                except requests.exceptions.SSLError as e:
                    return Response({
                        'error': 'SSL verification failed',
                        'details': str(e)
                    }, status=500)
 
                if flight_response_arrivals.status_code == 200:
                    flight_data_arrivals = flight_response_arrivals.json()
                    incoming_count += sum(
                        1 for offer in flight_data_arrivals.get('data', [])
                        for itinerary in offer.get('itineraries', [])
                        for segment in itinerary.get('segments', [])
                        if segment['arrival']['iataCode'] == origin
                    )
 
            response_data.append({
                'place': origin,
                'date': date,
                'numberOfDepartures': outgoing_count,
                'numberOfArrivals': incoming_count
            })
 
        # Serialize the response data
        response_serializer = FlightResponseSerializer(data=response_data, many=True)
        if not response_serializer.is_valid():
            return Response({'error': 'Failed to serialize response data', 'details': response_serializer.errors}, status=500)
       
        log_api_usage(request.user, request.path, request.data)
 
        # Return the filtered response
        return Response(response_serializer.data)
   
from .serializers import FlightSummaryRequestSerializer, FlightResponseSerializer
class FlightSummaryView(APIView):
    def post(self, request):
        # Deserialize the request data
        serializer = FlightSummaryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Invalid input', 'details': serializer.errors}, status=400)
 
        # Get validated data
        validated_data = serializer.validated_data
        if validated_data.get('flight') != 'summary':
            return Response({'error': 'Invalid input', 'details': 'Expected "flight": "summary"'}, status=400)
 
        # Get user-provided access token
        user_access_token = validated_data.get('access_token')
 
        # Define the current date
        date = datetime.today().strftime('%Y-%m-%d')
 
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
 
        # Define flight search parameters
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        flight_offers_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
        places_in_india = ['BLR', 'DEL', 'MAA', 'BOM', 'HYD', 'CCU']
        response_data = []
 
        # Calculate arrivals and departures for each place
        for place in places_in_india:
            outgoing_count, incoming_count = 0, 0
 
            # Departures from the place
            for destination in places_in_india:
                if place == destination:
                    continue
                search_params_departures = {
                    'originLocationCode': place,
                    'destinationLocationCode': destination,
                    'departureDate': date,
                    'adults': 1
                }
                flight_response_departures = requests.get(flight_offers_url, headers=headers, params=search_params_departures)
                if flight_response_departures.status_code == 200:
                    flight_data_departures = flight_response_departures.json()
                    outgoing_count += len(flight_data_departures.get('data', []))
 
            # Arrivals to the place
            for origin in places_in_india:
                if place == origin:
                    continue
                search_params_arrivals = {
                    'originLocationCode': origin,
                    'destinationLocationCode': place,
                    'departureDate': date,
                    'adults': 1
                }
                flight_response_arrivals = requests.get(flight_offers_url, headers=headers, params=search_params_arrivals)
                if flight_response_arrivals.status_code == 200:
                    flight_data_arrivals = flight_response_arrivals.json()
                    incoming_count += len(flight_data_arrivals.get('data', []))
 
            response_data.append({
                'place': place,
                'date': date,
                'numberOfDepartures': outgoing_count,
                'numberOfArrivals': incoming_count
            })
 
        # Serialize the response data
        response_serializer = FlightResponseSerializer(data=response_data, many=True)
 
        if not response_serializer.is_valid():
            return Response({'error': 'Failed to serialize response data', 'details': response_serializer.errors}, status=500)
 
        log_api_usage(request.user, request.path, request.data)
        # Return the filtered response
        return Response(response_serializer.data)
   










