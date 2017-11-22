from __future__ import unicode_literals
from django.db import models

class Device(models.Model):
    
    hostname = models.CharField(max_length=30, verbose_name="Hostname")
    ip_address = models.CharField(max_length=16, verbose_name="IP address")
    vendor = models.CharField(max_length=30, verbose_name="Vendor")