from django.urls import path
from .views import RegisterView
from .views import LoginView, RefreshTheAccessToken

 
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', RefreshTheAccessToken.as_view(), name='refresh'),

]



