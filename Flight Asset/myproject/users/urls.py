from django.urls import path
from .views import RegisterView
from .views import LoginView, RefreshTheAccessToken
from .views import FlightDetailsView

 
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', RefreshTheAccessToken.as_view(), name='refresh'),
    path('flight/', FlightDetailsView.as_view(), name='flight_details'),
]



