from django import forms


import re

from django import forms


class FirstPasswordChangeForm(forms.Form):
    new_password = forms.CharField(
        label="নতুন পাসওয়ার্ড",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "নতুন পাসওয়ার্ড লিখুন",
            }
        ),
    )

    confirm_password = forms.CharField(
        label="পাসওয়ার্ড নিশ্চিত করুন",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "পুনরায় পাসওয়ার্ড লিখুন",
            }
        ),
    )

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")

        errors = []

        # Length validation
        if len(password) < 8 or len(password) > 20:
            errors.append(
                "পাসওয়ার্ড কমপক্ষে ৮ এবং সর্বোচ্চ ২০ অক্ষরের হতে হবে।"
            )

        # Lowercase validation
        if not re.search(r"[a-z]", password):
            errors.append(
                "কমপক্ষে একটি ছোট হাতের অক্ষর (a-z) থাকতে হবে।"
            )

        # Uppercase validation
        if not re.search(r"[A-Z]", password):
            errors.append(
                "কমপক্ষে একটি বড় হাতের অক্ষর (A-Z) থাকতে হবে।"
            )

        # Digit validation
        if not re.search(r"[0-9]", password):
            errors.append(
                "অন্তত একটি সংখ্যা (0-9) থাকতে হবে।"
            )

        # Special character validation
        if not re.search(r"[!@#&()]", password):
            errors.append(
                "স্পেশাল ক্যারেক্টার (! @ # & ()) থাকতে হবে।"
            )

        if errors:
            raise forms.ValidationError(errors)

        return password

    def clean(self):
        cleaned = super().clean()

        password = cleaned.get("new_password")
        confirm_password = cleaned.get("confirm_password")

        # Check whether both passwords match
        if (
            password
            and confirm_password
            and password != confirm_password
        ):
            raise forms.ValidationError(
                "দুইটি পাসওয়ার্ড এক নয়।"
            )

        return cleaned
