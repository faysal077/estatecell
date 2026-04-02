# lands/forms.py
from django import forms
from .models import Land

class LandForm(forms.ModelForm):
    class Meta:
        model = Land
        fields = [
            'rd_office', 'division', 'district', 'upazila', 'mouza',
            'dag_no', 'khatian_no', 'area', 'owner_name'
        ]
        widgets = {
            'rd_office': forms.TextInput(attrs={'class': 'form-control'}),
            'division': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'upazila': forms.TextInput(attrs={'class': 'form-control'}),
            'mouza': forms.TextInput(attrs={'class': 'form-control'}),
            'dag_no': forms.TextInput(attrs={'class': 'form-control'}),
            'khatian_no': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.NumberInput(attrs={'class': 'form-control'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
