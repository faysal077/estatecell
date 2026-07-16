# lands/forms.py
from django import forms
from .models import Land
from esate_db.districts import DISTRICT_CHOICES_WITH_BN, DIVISION_NAMES

RD_OFFICE_CHOICES = [
    ("", "--------- Select RD Office ---------"),
    ("বিসিক আঞ্চলিক কার্যালয়, ঢাকা", "বিসিক আঞ্চলিক কার্যালয়, ঢাকা"),
    ("বিসিক আঞ্চলিক কার্যালয় চট্টগ্রাম", "বিসিক আঞ্চলিক কার্যালয় চট্টগ্রাম"),
    ("বিসিক আঞ্চলিক কার্যালয়, খুলনা", "বিসিক আঞ্চলিক কার্যালয়, খুলনা"),
    ("বিসিক আঞ্চলিক কার্যালয়, রাজশাহী", "বিসিক আঞ্চলিক কার্যালয়, রাজশাহী"),
]

class LandForm(forms.ModelForm):
    rd_office = forms.ChoiceField(
        choices=RD_OFFICE_CHOICES,
        widget=forms.Select(attrs={
            "class": "form-control"
        }),
        label="RD Office"
    )
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
    def clean_total_area(self):
        value = str(self.cleaned_data["total_area"])

        bangla_to_english = str.maketrans(
            "০১২৩৪৫৬৭৮৯",
            "0123456789"
        )

        value = value.translate(bangla_to_english)

        return value

    class Meta:
        model = Land
        
        fields = [
            "rd_office",
            "division",
            "district",
            "upazila",
            "owner_name",
            "total_area",
            "total_plots",
            "allocated_plots",
        ]
        widgets = {

            "upazila": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Upazila"
            }),
            "owner_name": forms.TextInput(attrs={
                "class":"form-control"
            }),

            "total_area": forms.NumberInput(attrs={
                "class":"form-control"
            }),

            "total_plots": forms.NumberInput(attrs={
                "class":"form-control",
                "id":"id_total_plots"
            }),

            "allocated_plots": forms.NumberInput(attrs={
                "class":"form-control",
                "id":"id_allocated_plots"
            }),

           

        }
