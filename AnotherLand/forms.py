from django import forms
from .models import AnotherLand
from esate_db.districts import DISTRICTS


DISTRICT_CHOICES = [
    (d["name"], d["name"])
    for d in DISTRICTS
]


class AnotherLandForm(forms.ModelForm):

    district = forms.ChoiceField(
        choices=DISTRICT_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )

    class Meta:
        model = AnotherLand

        fields = [
            "rd_office",
            "division",
            "district",
            "upazila",
            "office_name",
            "total_area",
        ]

        widgets = {

            "office_type": forms.Select(
                attrs={"class": "form-select"}
            ),

            "rd_office": forms.Select(
                attrs={"class": "form-select"}
            ),

            "division": forms.Select(
                attrs={"class": "form-select"}
            ),

            "upazila": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Upazila"
                }
            ),

            "office_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Office Name"
                }
            ),

            "total_area": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Total Area (Acres)",
                    "step": "0.01",
                    "min": "0"
                }
            ),
        }