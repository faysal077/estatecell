# lands/forms.py
from django import forms
from .models import Land
from esate_db.districts import DISTRICT_CHOICES_WITH_BN, DIVISION_NAMES


class LandForm(forms.ModelForm):
    district = forms.ChoiceField(
        choices=DISTRICT_CHOICES_WITH_BN,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="District"
    )
    division = forms.ChoiceField(
        choices=[(k, v) for k, v in DIVISION_NAMES.items()],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Division"
    )

    class Meta:
        model = Land
        fields = [
            'rd_office', 'division', 'district', 'upazila', 'mouza',
            'dag_no', 'khatian_no', 'area', 'owner_name'
        ]
        widgets = {
            'rd_office': forms.TextInput(attrs={'class': 'form-control'}),
            'upazila': forms.TextInput(attrs={'class': 'form-control'}),
            'mouza': forms.TextInput(attrs={'class': 'form-control'}),
            'dag_no': forms.TextInput(attrs={'class': 'form-control'}),
            'khatian_no': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.NumberInput(attrs={'class': 'form-control'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
