from rest_framework import serializers
from .models import Asset, AssetType, Location, RoomNumber, User

class AssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetType
        fields = ['id', 'name']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name']

class RoomNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomNumber
        fields = ['id', 'number']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name']

class AssetSerializer(serializers.ModelSerializer):
    asset_type = AssetTypeSerializer()
    location = LocationSerializer()
    room_number = RoomNumberSerializer()
    assigned_to = UserSerializer(allow_null=True)

    class Meta:
        model = Asset
        fields = ['id', 'asset_type', 'asset_number', 'location', 'room_number', 
                  'purchase_date', 'depreciation_date', 'is_allocated', 'assigned_to']