from __future__ import unicode_literals
from django.db import models

class Device(models.Model):
    hostname = models.CharField(max_length=30)
    ip_address = models.CharField(max_length=16)
    vendor = models.CharField(max_length=30)