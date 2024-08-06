from django.db import models
from django.contrib.auth.models import User
 
class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
 
    def __str__(self):
        return self.name
 
class FlightRequest(models.Model):
    request_type = models.CharField(max_length=100)
    date = models.DateField()
    iata_codes = models.JSONField()
 
class FlightSummary(models.Model):
    flight_request = models.ForeignKey(FlightRequest, on_delete=models.CASCADE)
    place = models.CharField(max_length=100)
    date = models.DateField()
    incoming_flights_count = models.IntegerField()
    outgoing_flights_count = models.IntegerField()
    total_flights = models.IntegerField()
 
from django.contrib.auth.models import User
from django.db import models
 
class APIUsageLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    request_data = models.TextField()
    response_data = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
 