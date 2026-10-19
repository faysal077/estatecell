
from django import forms

from .models import (
    EstatePageVerification,
    VerificationComment,
    VerificationStatus,
    WorkflowStatus,
)

from django import forms
from django.utils import timezone

from .models import ReportDeadline, ReportDeadlineExtension


class ReportDeadlineForm(forms.ModelForm):
    class Meta:
        model = ReportDeadline
        fields = ["report_key", "start_at", "end_at", "is_active"]
        widgets = {
            "start_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "report_key": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("start_at", "end_at"):
            self.fields[field].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_at")
        end = cleaned.get("end_at")

        if start and end and end <= start:
            raise forms.ValidationError(
                "শেষ সময় শুরুর সময়ের পরে হতে হবে।"
            )

        return cleaned


class DeadlineExtensionForm(forms.ModelForm):
    class Meta:
        model = ReportDeadlineExtension
        fields = ["new_end_at", "reason"]
        widgets = {
            "new_end_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "সময় বৃদ্ধির কারণ লিখুন",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_end_at"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_new_end_at(self):
        new_end = self.cleaned_data["new_end_at"]
        if new_end <= timezone.now():
            raise forms.ValidationError(
                "নতুন শেষ সময় ভবিষ্যতের হতে হবে।"
            )
        return new_end
class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class PageVerificationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EstatePageVerification
        fields = ["status"]
        widgets = {
            "status": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # NOT_APPLICABLE should only be selected when the page genuinely
        # does not apply to this estate and the workflow policy allows it.
        self.fields["status"].choices = [
            (VerificationStatus.VERIFIED, "Verified"),
            (VerificationStatus.NEEDS_CORRECTION, "Needs correction"),
        ]
        self.apply_bootstrap()


class VerificationCommentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = VerificationComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Enter verification comments...",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comment"].label = "Reviewer comment"
        self.fields["comment"].required = True
        self.apply_bootstrap()


class WorkflowActionForm(BootstrapFormMixin, forms.Form):
    ACTION_CHOICES = [
        ("submit", "Submit to next authority"),
        ("return", "Return for correction"),
        ("approve", "Approve"),
    ]

    action = forms.ChoiceField(choices=ACTION_CHOICES)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="A comment is required when returning a report.",
    )

    def __init__(self, *args, allowed_actions=None, **kwargs):
        super().__init__(*args, **kwargs)

        if allowed_actions is not None:
            self.fields["action"].choices = [
                choice for choice in self.ACTION_CHOICES
                if choice[0] in allowed_actions
            ]

        self.apply_bootstrap()

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get("action") == "return"
            and not cleaned_data.get("comment", "").strip()
        ):
            self.add_error(
                "comment",
                "A comment is required when returning a report.",
            )

        return cleaned_data
