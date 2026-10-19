
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from .models import (
    EstateReportSubmission,
    EstateWorkflowHistory,
    WorkflowAction,
    WorkflowStatus,
)
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    ReportDeadline,
    ReportDeadlineExtension,
    ReportSubmissionTracking,
)
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.core.exceptions import PermissionDenied
ROLE_ESTATE_OFFICER = "ESTATE_OFFICER"
ROLE_DATA_ENTRY = "DATA_ENTRY"
ROLE_RD_ADMIN = "RD_ADMIN"
ROLE_SUPER_ADMIN = "SUPER_ADMIN"

def get_accessible_estates(user):
    """
    Return industrial estates accessible to the logged-in user.
    Super Admin can access all estates.
    Other roles are restricted to estates assigned to them.
    """
    from industrial_estate.models import IndustrialEstate

    role = get_user_role(user)

    if user.is_superuser or role == ROLE_SUPER_ADMIN:
        return IndustrialEstate.objects.all()

    # Adjust these filters to match your actual model relationships.
    if role == ROLE_ESTATE_OFFICER:
        return IndustrialEstate.objects.filter(created_by=user)

    if role in (ROLE_DATA_ENTRY, ROLE_RD_ADMIN):
        # Replace with your project's actual RD/district access rules.
        return IndustrialEstate.objects.none()

    raise PermissionDenied("You cannot access these industrial estates.")


def get_user_role(user):
    if not user.is_authenticated:
        return ""

    try:
        profile = user.userprofile
    except Exception as exc:
        print(
            f"[ROLE DEBUG] Could not load profile for "
            f"{user.get_username()}: {type(exc).__name__}: {exc}"
        )
        return ""

    role = profile.role

    print(
        f"[ROLE DEBUG] username={user.get_username()}, "
        f"profile_id={profile.pk}, role={role!r}"
    )

    return str(role).strip().upper() if role else ""

def super_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Please log in first.")

        role = get_user_role(request.user)

        if not (
            request.user.is_superuser
            or role == ROLE_SUPER_ADMIN
        ):
            raise PermissionDenied(
                "Only Super Admin can access this page."
            )

        return view_func(request, *args, **kwargs)

    return wrapper



def get_open_deadline(report_key):
    """
    সময়সীমা না থাকলে বা সময় শেষ হলে Submit বন্ধ করবে।
    """
    deadline = get_object_or_404(
        ReportDeadline,
        report_key=report_key,
        is_active=True,
    )

    now = timezone.now()

    if now < deadline.start_at:
        raise PermissionDenied(
            "রিপোর্ট জমা দেওয়ার সময় এখনো শুরু হয়নি।"
        )

    if now >= deadline.end_at:
        raise PermissionDenied(
            "রিপোর্ট জমা দেওয়ার সময়সীমা শেষ হয়েছে। "
            "Super Admin সময় বাড়ালে আবার জমা দিতে পারবেন।"
        )

    return deadline


def record_report_submission(*, deadline, estate, user):
    """
    মূল রিপোর্ট সফলভাবে সংরক্ষিত হওয়ার পর কল করবেন।
    """
    now = timezone.now()

    # DB-তে লেখার সময়ও Deadline পরীক্ষা করুন।
    deadline.refresh_from_db()

    if not deadline.is_active:
        raise PermissionDenied("এই রিপোর্টের জমা বন্ধ রয়েছে।")

    if not (deadline.start_at <= now < deadline.end_at):
        raise PermissionDenied(
            "সময়সীমার বাইরে রিপোর্ট জমা দেওয়া যাবে না।"
        )

    tracking, _ = ReportSubmissionTracking.objects.get_or_create(
        deadline=deadline,
        estate=estate,
    )

    tracking.status = ReportSubmissionTracking.Status.SUBMITTED
    tracking.submitted_by = user
    tracking.submitted_at = now
    tracking.save(
        update_fields=[
            "status",
            "submitted_by",
            "submitted_at",
            "updated_at",
        ]
    )

    return tracking


def extend_deadline(*, deadline, form, user):
    """
    Extension এবং deadline update একই transaction-এ সংরক্ষণ করুন।
    """
    from django.db import transaction

    with transaction.atomic():
        locked = ReportDeadline.objects.select_for_update().get(
            pk=deadline.pk
        )

        new_end = form.cleaned_data["new_end_at"]

        if new_end <= locked.end_at:
            raise ValueError(
                "নতুন শেষ সময় বর্তমান শেষ সময়ের পরে হতে হবে।"
            )

        ReportDeadlineExtension.objects.create(
            deadline=locked,
            previous_end_at=locked.end_at,
            new_end_at=new_end,
            reason=form.cleaned_data["reason"],
            extended_by=user,
        )

        locked.end_at = new_end
        locked.is_active = True
        locked.save(update_fields=["end_at", "is_active", "updated_at"])

    return locked

# def get_user_role(user):
#     """
#     Integration point:
#     Adjust this function to match your project's actual role model.
#     It supports a direct user.role or user.profile.role field.
#     """
#     role = getattr(user, "role", None)

#     if role is None and hasattr(user, "profile"):
#         role = getattr(user.profile, "role", None)

#     return str(getattr(role, "value", role) or "").upper()


def allowed_actions_for(user, submission):
    role = get_user_role(user)
    status = submission.status

    if role == ROLE_ESTATE_OFFICER:
        if status in (
            WorkflowStatus.DRAFT,
            WorkflowStatus.RETURNED_TO_ESTATE,
        ):
            return ["submit"]
        return []

    if role == ROLE_DATA_ENTRY:
        if status == WorkflowStatus.SUBMITTED_TO_DISTRICT:
            return ["submit", "return"]
        if status == WorkflowStatus.RETURNED_TO_DISTRICT:
            return ["submit", "return"]
        return []

    if role == ROLE_RD_ADMIN:
        if status == WorkflowStatus.SUBMITTED_TO_RD:
            return ["submit", "return"]
        return []

    if role == ROLE_SUPER_ADMIN:
        if status == WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN:
            return ["approve", "return"]
        if status == WorkflowStatus.RETURNED_BY_SUPER_ADMIN:
            return ["submit", "return", "approve"]
        return []

    return []


def _next_status(user, submission, action):
    role = get_user_role(user)
    status = submission.status

    if action == "submit":
        if role == ROLE_ESTATE_OFFICER and status in (
            WorkflowStatus.DRAFT,
            WorkflowStatus.RETURNED_TO_ESTATE,
        ):
            return WorkflowStatus.SUBMITTED_TO_DISTRICT

        if role == ROLE_DATA_ENTRY and status in (
            WorkflowStatus.SUBMITTED_TO_DISTRICT,
            WorkflowStatus.RETURNED_TO_DISTRICT,
        ):
            return WorkflowStatus.SUBMITTED_TO_RD

        if role == ROLE_RD_ADMIN and status == WorkflowStatus.SUBMITTED_TO_RD:
            return WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN

        if (
            role == ROLE_SUPER_ADMIN
            and status == WorkflowStatus.RETURNED_BY_SUPER_ADMIN
        ):
            return WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN

    elif action == "return":
        if role == ROLE_DATA_ENTRY and status in (
            WorkflowStatus.SUBMITTED_TO_DISTRICT,
            WorkflowStatus.RETURNED_TO_DISTRICT,
        ):
            return WorkflowStatus.RETURNED_TO_ESTATE

        if role == ROLE_RD_ADMIN and status == WorkflowStatus.SUBMITTED_TO_RD:
            return WorkflowStatus.RETURNED_TO_DISTRICT

        if (
            role == ROLE_SUPER_ADMIN
            and status == WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN
        ):
            return WorkflowStatus.RETURNED_BY_SUPER_ADMIN

    elif action == "approve":
        if (
            role == ROLE_SUPER_ADMIN
            and status == WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN
        ):
            return WorkflowStatus.APPROVED

    raise PermissionDenied("This workflow action is not permitted.")


@transaction.atomic
def perform_workflow_action(
    *,
    submission,
    user,
    action,
    comment="",
):
    """
    Must only be called after the view has checked that the user may
    access this estate and act at the current workflow stage.
    """
    permitted_actions = allowed_actions_for(user, submission)

    if action not in permitted_actions:
        raise PermissionDenied("You cannot perform this action.")

    if action == "return" and not comment.strip():
        raise ValidationError("A comment is required when returning a report.")

    previous_status = submission.status
    next_status = _next_status(user, submission, action)

    submission.status = next_status
    submission.last_action_by = user
    submission.last_action_at = timezone.now()

    if action == "submit":
        submission.submitted_by = user
        submission.submitted_at = timezone.now()

    if action == "approve":
        submission.approved_by = user
        submission.approved_at = timezone.now()

    submission.save()

    action_map = {
        "submit": WorkflowAction.FORWARDED,
        "return": WorkflowAction.CORRECTION_REQUESTED,
        "approve": WorkflowAction.APPROVED,
    }

    EstateWorkflowHistory.objects.create(
        submission=submission,
        actor=user,
        action=action_map[action],
        from_status=previous_status,
        to_status=next_status,
        comment=comment.strip(),
    )

    return submission
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect

from estate_verification.services import (
    get_open_deadline,
    record_report_submission,
)


@transaction.atomic
def submit_industrial_units_report(request, estate):
    if request.method != "POST":
        raise PermissionDenied

    # 1. ব্যবহারকারী এই estate-এ কাজ করার অনুমতি রাখেন কি না,
    #    আপনার বিদ্যমান access-control অনুযায়ী যাচাই করুন।

    # 2. Deadline যাচাই করুন। সময় শেষ হলে এখানে Submit বন্ধ হবে।
    deadline = get_open_deadline("industrial_units")

    # 3. আপনার বিদ্যমান শিল্প ইউনিটের ফর্ম validation ও save
    #    এখানে করতে হবে।
    #
    # form = ExistingIndustrialUnitForm(request.POST, ...)
    # if not form.is_valid():
    #     return render(...)
    # form.save()

    # 4. মূল রিপোর্ট সফলভাবে সংরক্ষিত হওয়ার পর ট্র্যাকিং আপডেট করুন।
    record_report_submission(
        deadline=deadline,
        estate=estate,
        user=request.user,
    )

    messages.success(request, "রিপোর্ট জমা হয়েছে।")
    return redirect("industrial_estate:YOUR_EXISTING_REPORT_URL_NAME")