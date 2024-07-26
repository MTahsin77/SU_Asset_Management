from django import forms
from .models import Asset, User, Allocation

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_type', 'asset_number', 'location', 'room_number', 'purchase_date', 'depreciation_date']

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name']

class AllocationForm(forms.ModelForm):
    class Meta:
        model = Allocation
        fields = ['user', 'asset', 'assigned_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(is_allocated=False)

class DeallocationForm(forms.Form):
    return_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))