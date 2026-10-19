from django.db import models

# Create your models here.

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ReportDeadline(models.Model):
    REPORT_CHOICES = [
        ("industrial_units", "শিল্প ইউনিটের তথ্য"),
        ("land_plots", "জমি ও প্লটের তথ্য"),
        ("estate_general", "শিল্প এস্টেটের সাধারণ তথ্য"),
        ("infrastructure", "অবকাঠামো ও ইউটিলিটির তথ্য"),
    ]

    report_key = models.CharField(
        max_length=50,
        choices=REPORT_CHOICES,
        unique=True,
        verbose_name="রিপোর্ট",
    )
    start_at = models.DateTimeField(verbose_name="শুরুর সময়")
    end_at = models.DateTimeField(verbose_name="শেষ সময়")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_report_deadlines",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["end_at"]
        verbose_name = "রিপোর্ট জমাদানের সময়সীমা"
        verbose_name_plural = "রিপোর্ট জমাদানের সময়সীমা"

    def clean(self):
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({
                "end_at": "শেষ সময় শুরুর সময়ের পরে হতে হবে।"
            })

    @property
    def is_open(self):
        now = timezone.now()
        return (
            self.is_active
            and self.start_at <= now < self.end_at
        )

    @property
    def is_upcoming(self):
        return self.is_active and timezone.now() < self.start_at

    @property
    def is_expired(self):
        return timezone.now() >= self.end_at

    def __str__(self):
        return self.get_report_key_display()


class ReportDeadlineExtension(models.Model):
    deadline = models.ForeignKey(
        ReportDeadline,
        on_delete=models.PROTECT,
        related_name="extensions",
    )
    previous_end_at = models.DateTimeField()
    new_end_at = models.DateTimeField()
    reason = models.TextField()
    extended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "সময় বৃদ্ধির ইতিহাস"
        verbose_name_plural = "সময় বৃদ্ধির ইতিহাস"

    def __str__(self):
        return f"{self.deadline} — {self.new_end_at}"


class ReportSubmissionTracking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "জমা দেওয়া হয়নি"
        SUBMITTED = "SUBMITTED", "সময়মতো জমা"
        LATE_SUBMITTED = "LATE_SUBMITTED", "দেরিতে জমা"

    deadline = models.ForeignKey(
        ReportDeadline,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    estate = models.ForeignKey(
        "industrial_estate.IndustrialEstate",
        on_delete=models.PROTECT,
        related_name="report_deadline_submissions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["deadline", "estate"],
                name="unique_deadline_estate_submission",
            )
        ]
        ordering = ["deadline__end_at"]

    def __str__(self):
        return f"{self.deadline} — {self.estate}"

class WorkflowStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED_TO_DISTRICT = (
        "SUBMITTED_TO_DISTRICT", "Submitted to Data Entry Officer"
    )
    RETURNED_TO_ESTATE = "RETURNED_TO_ESTATE", "Returned to Estate Officer"
    SUBMITTED_TO_RD = "SUBMITTED_TO_RD", "Submitted to RD Admin"
    RETURNED_TO_DISTRICT = "RETURNED_TO_DISTRICT", "Returned to Data Entry Officer"
    SUBMITTED_TO_SUPER_ADMIN = (
        "SUBMITTED_TO_SUPER_ADMIN", "Submitted to Super Admin"
    )
    RETURNED_BY_SUPER_ADMIN = (
        "RETURNED_BY_SUPER_ADMIN", "Returned by Super Admin"
    )
    APPROVED = "APPROVED", "Approved"


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    VERIFIED = "VERIFIED", "Verified"
    NEEDS_CORRECTION = "NEEDS_CORRECTION", "Needs correction"
    NOT_APPLICABLE = "NOT_APPLICABLE", "Not applicable"


class WorkflowAction(models.TextChoices):
    CREATED = "CREATED", "Created"
    SUBMITTED = "SUBMITTED", "Submitted"
    VERIFIED = "VERIFIED", "Verified"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED", "Correction requested"
    EDITED = "EDITED", "Data edited"
    FORWARDED = "FORWARDED", "Forwarded"
    APPROVED = "APPROVED", "Approved"
    REOPENED = "REOPENED", "Reopened"


class EstateReportSubmission(models.Model):
    """
    One active workflow record per industrial estate.
    The actual estate data remains in industrial_estate models.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    estate = models.OneToOneField(
        "industrial_estate.IndustrialEstate",
        on_delete=models.PROTECT,
        related_name="verification_submission",
    )

    status = models.CharField(
        max_length=40,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
        db_index=True,
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estate_verification_submissions",
    )

    submitted_at = models.DateTimeField(null=True, blank=True)

    current_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_estate_verifications",
    )

    last_action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_action_estate_verifications",
    )

    last_action_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_estate_verifications",
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Estate report submission"
        verbose_name_plural = "Estate report submissions"

    def __str__(self):
        return f"{self.estate} — {self.get_status_display()}"

    @property
    def is_approved(self):
        return self.status == WorkflowStatus.APPROVED


class EstatePageVerification(models.Model):
    """
    Verification status for one page in one estate submission.

    page_key must be a stable key such as 'general_information'
    or 'water_supply'. page_title and group_title are display labels.
    """

    submission = models.ForeignKey(
        EstateReportSubmission,
        on_delete=models.CASCADE,
        related_name="page_verifications",
    )

    page_key = models.SlugField(max_length=100)
    page_title = models.CharField(max_length=200)
    group_key = models.SlugField(max_length=100)
    group_title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_estate_pages",
    )

    verified_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["group_key", "order", "page_title"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "page_key"],
                name="unique_submission_page_verification",
            )
        ]
        indexes = [
            models.Index(fields=["submission", "status"]),
            models.Index(fields=["group_key", "order"]),
        ]

    def __str__(self):
        return f"{self.submission.estate} — {self.page_title}"

    def mark_verified(self, user):
        self.status = VerificationStatus.VERIFIED
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "verified_by",
                "verified_at",
                "updated_at",
            ]
        )


class VerificationComment(models.Model):
    """
    Comments may apply to an individual page or the entire submission.
    Comments are retained as history rather than overwritten.
    """

    submission = models.ForeignKey(
        EstateReportSubmission,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    page_verification = models.ForeignKey(
        EstatePageVerification,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="estate_verification_comments",
    )

    stage = models.CharField(max_length=40, choices=WorkflowStatus.choices)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def clean(self):
        if (
            self.page_verification_id
            and self.page_verification.submission_id != self.submission_id
        ):
            raise ValidationError(
                "The selected page does not belong to this submission."
            )

    def __str__(self):
        return f"Comment on {self.submission.estate} at {self.created_at:%Y-%m-%d}"


class EstateWorkflowHistory(models.Model):
    """
    Immutable-style audit trail for workflow transitions.
    """

    submission = models.ForeignKey(
        EstateReportSubmission,
        on_delete=models.CASCADE,
        related_name="history",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="estate_workflow_actions",
    )

    action = models.CharField(max_length=30, choices=WorkflowAction.choices)
    from_status = models.CharField(
        max_length=40, choices=WorkflowStatus.choices, blank=True
    )
    to_status = models.CharField(
        max_length=40, choices=WorkflowStatus.choices, blank=True
    )
    comment = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.submission.estate} — {self.get_action_display()}"


class EstateFieldChangeLog(models.Model):
    """
    Records changes made to the actual estate data by a reviewer.
    This model stores the audit information; the editing view must create
    a log entry whenever it changes a field.
    """

    submission = models.ForeignKey(
        EstateReportSubmission,
        on_delete=models.CASCADE,
        related_name="field_changes",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="estate_field_changes",
    )

    model_label = models.CharField(max_length=150)
    object_pk = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)

    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["submission", "created_at"]),
            models.Index(fields=["model_label", "object_pk"]),
        ]

    def __str__(self):
        return (
            f"{self.model_label}.{self.field_name} "
            f"— {self.submission.estate}"
        )
