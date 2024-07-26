from django.db import models
from django.utils import timezone

class User(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Asset(models.Model):
    asset_type = models.CharField(max_length=50)
    asset_number = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    depreciation_date = models.DateField(blank=True, null=True)
    is_allocated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.asset_type} - {self.asset_number}"

class Allocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    assigned_date = models.DateField(default=timezone.now)
    return_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.asset} allocated to {self.user}"