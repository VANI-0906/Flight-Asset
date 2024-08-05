from django.db import models
 
# Create your models here.

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
