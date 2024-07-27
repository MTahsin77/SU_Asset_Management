from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User as AuthUser
from datetime import timedelta

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name

class AssetType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class RoomNumber(models.Model):
    number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.number

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Asset(models.Model):
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)
    asset_number = models.CharField(max_length=50, unique=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    room_number = models.ForeignKey(RoomNumber, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    purchase_date = models.DateField()
    depreciation_date = models.DateField(editable=False)
    purchase_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    model = models.CharField(max_length=100)
    is_allocated = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sticker_deployed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.purchase_date:
            self.depreciation_date = self.purchase_date + timedelta(days=5*365)
            years_passed = (timezone.now().date() - self.purchase_date).days / 365.25
            depreciation_factor = max(0, 1 - (0.2 * years_passed))
            self.current_value = self.purchase_value * depreciation_factor
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_type} - {self.asset_number}"

class Allocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    assigned_date = models.DateField(default=timezone.now)
    return_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.asset} allocated to {self.user}"