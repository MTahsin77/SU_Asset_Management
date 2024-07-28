from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User as AuthUser
from datetime import timedelta
from decimal import Decimal

class AssetType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class RoomNumber(models.Model):
    number = models.CharField(max_length=255)

    def __str__(self):
        return self.number

class Department(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class User(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True, null=True)  # Make email optional

    def __str__(self):
        return self.name

class Asset(models.Model):
    asset_number = models.CharField(max_length=50, unique=True)
    asset_type = models.ForeignKey('AssetType', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)
    room_number = models.ForeignKey('RoomNumber', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    depreciation_date = models.DateField(null=True, blank=True)
    purchase_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_allocated = models.BooleanField(default=False)
    assigned_to = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    sticker_deployed = models.BooleanField(default=False)

    def __str__(self):
        asset_type = self.asset_type.name if self.asset_type else "Unknown"
        purchase_date = self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else "Unknown"
        current_value = f"£{self.current_value}" if self.current_value is not None else "Unknown"
        return f"{self.asset_number} - {asset_type} - (Purchased: {purchase_date}, Current Value: {current_value})"

    def save(self, *args, **kwargs):
        if self.purchase_date:
            self.depreciation_date = self.purchase_date + timedelta(days=5*365)
            years_passed = (timezone.now().date() - self.purchase_date).days / 365.25
            depreciation_factor = max(Decimal('0'), Decimal('1') - (Decimal('0.2') * Decimal(str(years_passed))))
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