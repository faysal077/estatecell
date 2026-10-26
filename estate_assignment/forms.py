from django import forms
from django.core.exceptions import ValidationError

from accounts.models import UserProfile, UserRole
from industrial_estate.models import IndustrialEstate


class EstateOfficerAssignmentForm(forms.Form):
    estate_id = forms.IntegerField(widget=forms.HiddenInput)

    officer = forms.ModelChoiceField(
        queryset=UserProfile.objects.none(),
        required=True,
        label="Estate Officer",
        empty_label="Select an available Estate Officer",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, estate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.estate = estate

        available = UserProfile.objects.filter(
            role=UserRole.ESTATE_OFFICER,
            user__is_active=True,
            assigned_estate__isnull=True,
        ).select_related("user")

        # Keep the currently assigned officer available when editing.
        if estate is not None:
            current = UserProfile.objects.filter(
                role=UserRole.ESTATE_OFFICER,
                assigned_estate=estate,
                user__is_active=True,
            ).select_related("user")

            available = (available | current).distinct()

        self.fields["officer"].queryset = available.order_by(
            "full_name", "user__username"
        )

        if estate is not None:
            self.fields["estate_id"].initial = estate.pk

    def clean_estate_id(self):
        estate_id = self.cleaned_data["estate_id"]

        if self.estate is None or estate_id != self.estate.pk:
            raise ValidationError("Invalid estate selection.")

        return estate_id

    def clean(self):
        cleaned = super().clean()
        officer = cleaned.get("officer")

        if not officer or not self.estate:
            return cleaned

        if officer.role != UserRole.ESTATE_OFFICER:
            raise ValidationError(
                "Only Estate Officers can be assigned."
            )

        # Do not allow one officer to be assigned to multiple estates.
        if (
            officer.assigned_estate_id
            and officer.assigned_estate_id != self.estate.pk
        ):
            self.add_error(
                "officer",
                "This officer is already assigned to another estate.",
            )

        # Do not allow two officers to be assigned to the same estate.
        other_assignment = UserProfile.objects.filter(
            role=UserRole.ESTATE_OFFICER,
            assigned_estate=self.estate,
        ).exclude(pk=officer.pk)

        if other_assignment.exists():
            self.add_error(
                "officer",
                "This estate already has another assigned officer.",
            )

        return cleaned