from django.db import models


class Vehicle(models.Model):
    identifier = models.CharField(max_length=17, primary_key=True, unique=True)


class Ecu(models.Model):
    identifier = models.CharField(max_length=64, primary_key=True, unique=True)
    public_key = models.TextField()
    primary = models.BooleanField()
    vehicle_id = models.ForeignKey('Vehicle', models.PROTECT)
