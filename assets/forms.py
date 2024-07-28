from django import forms
from .models import Asset, Department, User, Allocation, AssetType, Location, RoomNumber

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_type', 'asset_number', 'location', 'room_number', 'department',
                  'purchase_date', 'purchase_value', 'assigned_to', 'sticker_deployed']
        widgets = {
            'asset_type': forms.Select(attrs={'class': 'form-control select2'}),
            'asset_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control select2'}),
            'room_number': forms.Select(attrs={'class': 'form-control select2'}),
            'department': forms.Select(attrs={'class': 'form-control select2'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control flatpickr-input', 'type': 'text'}),
            'purchase_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control select2'}),
            'sticker_deployed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email']  # Include email, but it will be optional
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class AllocationForm(forms.ModelForm):
    class Meta:
        model = Allocation
        fields = ['user', 'asset', 'assigned_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(is_allocated=False)

class DeallocationForm(forms.Form):
    return_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class AssetTypeForm(forms.ModelForm):
    class Meta:
        model = AssetType
        fields = ['name']

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name']

class RoomNumberForm(forms.ModelForm):
    class Meta:
        model = RoomNumber
        fields = ['number']

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='Select a CSV file')