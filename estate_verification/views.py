from django.http import request
from django.shortcuts import render

# Create your views here.

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .services import super_admin_required, extend_deadline

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .services import (
    get_user_role,
    ROLE_SUPER_ADMIN,
    ROLE_ESTATE_OFFICER,
    ROLE_DATA_ENTRY,
    ROLE_RD_ADMIN,
)
from .forms import (
    PageVerificationForm,
    VerificationCommentForm,
    WorkflowActionForm,
)
from .models import (
    EstatePageVerification,
    EstateReportSubmission,
    EstateWorkflowHistory,
    VerificationComment,
    VerificationStatus,
    WorkflowStatus,
)
from .services import (
    ROLE_DATA_ENTRY,
    ROLE_ESTATE_OFFICER,
    ROLE_RD_ADMIN,
    ROLE_SUPER_ADMIN,
    allowed_actions_for,
    get_user_role,
    perform_workflow_action,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ReportDeadlineForm, DeadlineExtensionForm
from .models import (
    ReportDeadline,
    ReportDeadlineExtension,
    ReportSubmissionTracking,
)
@login_required
@super_admin_required
def deadline_management(request):
    form = ReportDeadlineForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        deadline = form.save(commit=False)
        deadline.created_by = request.user
        deadline.save()

        messages.success(
            request,
            "রিপোর্টের সময়সীমা সফলভাবে সংরক্ষণ করা হয়েছে।",
        )
        return redirect("estate_verification:deadline_management")

    deadlines = ReportDeadline.objects.annotate(
        total_estates=Count("submissions", distinct=True),
        submitted_count=Count(
            "submissions",
            filter=Q(
                submissions__status=(
                    ReportSubmissionTracking.Status.SUBMITTED
                )
            ),
            distinct=True,
        ),
    )

    return render(
        request,
        "estate_verification/deadline_management.html",
        {
            "form": form,
            "deadlines": deadlines,
            "now": timezone.now(),
        },
    )
from .services import super_admin_required, extend_deadline

def _accessible_submission_or_404(user, submission_id):
    accessible_estates = get_accessible_estates(user)

    return get_object_or_404(
        EstateReportSubmission.objects.select_related("estate"),
        pk=submission_id,
        estate__in=accessible_estates,
    )


def _can_review(user, submission):
    """
    Stage-level role check. Estate assignment and RD assignment must also
    be checked against your actual user/estate relationship fields.
    """
    role = get_user_role(user)

    if role == ROLE_SUPER_ADMIN:
        return True

    if role == ROLE_DATA_ENTRY:
        return submission.status in (
            WorkflowStatus.SUBMITTED_TO_DISTRICT,
            WorkflowStatus.RETURNED_TO_DISTRICT,
        )

    if role == ROLE_RD_ADMIN:
        return submission.status in (
            WorkflowStatus.SUBMITTED_TO_RD,
            WorkflowStatus.RETURNED_BY_SUPER_ADMIN,
        )

    return False



from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from .models import EstateReportSubmission, WorkflowStatus
from .services import (
    get_user_role,
    get_accessible_estates,
    ROLE_SUPER_ADMIN,
    ROLE_ESTATE_OFFICER,
    ROLE_DATA_ENTRY,
    ROLE_RD_ADMIN,
)
@login_required
def dashboard(request):
    role = get_user_role(request.user)
    print("Username:", request.user.get_username())
    print("User model:", type(request.user))
    print("Direct role:", getattr(request.user, "role", "FIELD_NOT_FOUND"))
    print("Profile:", getattr(request.user, "profile", "PROFILE_NOT_FOUND"))
    print("Detected role:", repr(role))

    allowed_roles = {
        ROLE_SUPER_ADMIN,
        ROLE_ESTATE_OFFICER,
        ROLE_DATA_ENTRY,
        ROLE_RD_ADMIN,
    }

    if not (
        request.user.is_superuser
        or role in allowed_roles
    ):
        raise PermissionDenied(
            f"You cannot access this dashboard. Detected role: {role!r}"
        )

    # Super Admin can see all submissions.
    if request.user.is_superuser or role == ROLE_SUPER_ADMIN:
        submissions = (
            EstateReportSubmission.objects
            .all()
            .select_related("estate", "current_assignee")
            .prefetch_related("page_verifications")
        )
    else:
        accessible_estates = get_accessible_estates(request.user)

        submissions = (
            EstateReportSubmission.objects
            .filter(estate__in=accessible_estates)
            .select_related("estate", "current_assignee")
            .prefetch_related("page_verifications")
        )

    if role == ROLE_ESTATE_OFFICER:
        submissions = submissions.filter(
            status__in=[
                WorkflowStatus.DRAFT,
                WorkflowStatus.RETURNED_TO_ESTATE,
                WorkflowStatus.SUBMITTED_TO_DISTRICT,
                WorkflowStatus.SUBMITTED_TO_RD,
                WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN,
                WorkflowStatus.APPROVED,
            ]
        )

    elif role == ROLE_DATA_ENTRY:
        submissions = submissions.filter(
            status__in=[
                WorkflowStatus.SUBMITTED_TO_DISTRICT,
                WorkflowStatus.RETURNED_TO_DISTRICT,
            ]
        )

    elif role == ROLE_RD_ADMIN:
        submissions = submissions.filter(
            status__in=[
                WorkflowStatus.SUBMITTED_TO_RD,
                WorkflowStatus.RETURNED_BY_SUPER_ADMIN,
            ]
        )

    context = {
        "submissions": submissions,
        "role": role,
        "total_submissions": submissions.count(),
        "pending_submissions": submissions.exclude(
            status=WorkflowStatus.APPROVED
        ).count(),
        "approved_submissions": submissions.filter(
            status=WorkflowStatus.APPROVED
        ).count(),
    }
    
    return render(
        request,
        "estate_verification/dashboard.html",
        context,
    )



@login_required
def estate_review(request, submission_id):
    submission = _accessible_submission_or_404(
        request.user, submission_id
    )

    role = get_user_role(request.user)


    is_estate_officer = (
        role == ROLE_ESTATE_OFFICER
        and submission.status in (
            WorkflowStatus.DRAFT,
            WorkflowStatus.RETURNED_TO_ESTATE,
            WorkflowStatus.SUBMITTED_TO_DISTRICT,
            WorkflowStatus.SUBMITTED_TO_RD,
            WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN,
            WorkflowStatus.APPROVED,
        )
    )

    if not is_estate_officer and not _can_review(request.user, submission):
        raise PermissionDenied("You cannot review this submission.")

    page_verifications = submission.page_verifications.all()

    verified_count = page_verifications.filter(
        status=VerificationStatus.VERIFIED
    ).count()

    context = {
        "submission": submission,
        "estate": submission.estate,
        "page_verifications": page_verifications,
        "comments": submission.comments.select_related(
            "author", "page_verification"
        ),
        "history": submission.history.select_related("actor"),
        "verified_count": verified_count,
        "total_pages": page_verifications.count(),
        "workflow_form": WorkflowActionForm(
            allowed_actions=allowed_actions_for(request.user, submission)
        ),
    }

    return render(
        request,
        "estate_verification/estate_review.html",
        context,
    )


@login_required
@require_POST
def verify_page(request, submission_id, page_id):
    submission = _accessible_submission_or_404(
        request.user, submission_id
    )

    if not _can_review(request.user, submission):
        raise PermissionDenied("You cannot verify pages at this stage.")

    page = get_object_or_404(
        EstatePageVerification,
        pk=page_id,
        submission=submission,
    )

    form = PageVerificationForm(request.POST, instance=page)

    if form.is_valid():
        page = form.save(commit=False)
        page.verified_by = request.user

        if page.status == VerificationStatus.VERIFIED:
            from django.utils import timezone
            page.verified_at = timezone.now()
        else:
            page.verified_at = None

        page.save()

        EstateWorkflowHistory.objects.create(
            submission=submission,
            actor=request.user,
            action="VERIFIED",
            from_status=submission.status,
            to_status=submission.status,
            comment=f"Page checklist updated: {page.page_title} — "
                    f"{page.get_status_display()}",
            metadata={
                "page_id": page.pk,
                "page_key": page.page_key,
                "page_status": page.status,
            },
        )

        messages.success(request, "Page verification status saved.")
    else:
        messages.error(request, "Please correct the verification form.")

    return redirect(
        "estate_verification:estate_review",
        submission_id=submission.pk,
    )


@login_required
@require_POST
def add_comment(request, submission_id):
    submission = _accessible_submission_or_404(
        request.user, submission_id
    )

    role = get_user_role(request.user)

    if role == ROLE_ESTATE_OFFICER:
        can_comment = submission.status in (
            WorkflowStatus.DRAFT,
            WorkflowStatus.RETURNED_TO_ESTATE,
        )
    else:
        can_comment = _can_review(request.user, submission)

    if not can_comment:
        raise PermissionDenied("You cannot comment on this submission.")

    form = VerificationCommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.submission = submission
        comment.author = request.user
        comment.stage = submission.status

        page_id = request.POST.get("page_verification_id")
        if page_id:
            comment.page_verification = get_object_or_404(
                EstatePageVerification,
                pk=page_id,
                submission=submission,
            )

        comment.save()
        messages.success(request, "Comment added.")
    else:
        messages.error(request, "Please enter a valid comment.")

    return redirect(
        "estate_verification:estate_review",
        submission_id=submission.pk,
    )


@login_required
@require_POST
def workflow_action(request, submission_id):
    submission = _accessible_submission_or_404(
        request.user, submission_id
    )

    form = WorkflowActionForm(
        request.POST,
        allowed_actions=allowed_actions_for(request.user, submission),
    )

    if not form.is_valid():
        messages.error(request, "Please review the workflow action and comment.")
        return redirect(
            "estate_verification:estate_review",
            submission_id=submission.pk,
        )

    action = form.cleaned_data["action"]
    comment_text = form.cleaned_data["comment"].strip()

    # A reviewer must leave a comment when forwarding a report.
    if action == "submit" and get_user_role(request.user) != ROLE_ESTATE_OFFICER:
        if not comment_text:
            messages.error(
                request,
                "Please add your review comment before forwarding.",
            )
            return redirect(
                "estate_verification:estate_review",
                submission_id=submission.pk,
            )

    # Require every configured page to have a verification record and
    # be verified before forwarding. Page registry initialization must
    # be implemented before enabling this enforcement in production.
    if action in ("submit", "approve"):
        pages = submission.page_verifications.all()

        if not pages.exists():
            messages.error(
                request,
                "No page checklist has been configured for this submission.",
            )
            return redirect(
                "estate_verification:estate_review",
                submission_id=submission.pk,
            )

        incomplete_pages = pages.exclude(
            status__in=[
                VerificationStatus.VERIFIED,
                VerificationStatus.NOT_APPLICABLE,
            ]
        )

        if incomplete_pages.exists():
            messages.error(
                request,
                "All applicable pages must be verified before this action.",
            )
            return redirect(
                "estate_verification:estate_review",
                submission_id=submission.pk,
            )

    try:
        with transaction.atomic():
            if comment_text:
                VerificationComment.objects.create(
                    submission=submission,
                    author=request.user,
                    stage=submission.status,
                    comment=comment_text,
                )

            perform_workflow_action(
                submission=submission,
                user=request.user,
                action=action,
                comment=comment_text,
            )

        messages.success(request, "Workflow action completed.")

    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, str(exc))

    return redirect(
        "estate_verification:dashboard"
    )


@login_required
def submission_history(request, submission_id):
    submission = _accessible_submission_or_404(
        request.user, submission_id
    )

    role = get_user_role(request.user)
    if role != ROLE_SUPER_ADMIN and not _can_review(request.user, submission):
        if role != ROLE_ESTATE_OFFICER:
            raise PermissionDenied("You cannot view this history.")

    history = submission.history.select_related("actor")
    field_changes = submission.field_changes.select_related("actor")
    comments = submission.comments.select_related(
        "author", "page_verification"
    )

    return render(
        request,
        "estate_verification/submission_history.html",
        {
            "submission": submission,
            "history": history,
            "field_changes": field_changes,
            "comments": comments,
        },
    )
@login_required
@super_admin_required
def deadline_extend(request, pk):
    deadline = get_object_or_404(ReportDeadline, pk=pk)
    form = DeadlineExtensionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            extend_deadline(
                deadline=deadline,
                form=form,
                user=request.user,
            )
        except ValueError as exc:
            form.add_error("new_end_at", str(exc))
        else:
            messages.success(
                request,
                "সময়সীমা বাড়ানো হয়েছে। Estate Officer-দের "
                "ড্যাশবোর্ডে নতুন সময় দেখানো হবে।",
            )
            return redirect("estate_verification:deadline_management")

    extensions = deadline.extensions.select_related(
        "extended_by"
    ).all()

    return render(
        request,
        "estate_verification/deadline_extend.html",
        {
            "deadline": deadline,
            "form": form,
            "extensions": extensions,
        },
    )

@login_required
def report_deadline_dashboard(request):
    estates = get_accessible_estates(request.user)

    deadlines = ReportDeadline.objects.filter(
        is_active=True
    ).order_by("end_at")

    rows = []

    for deadline in deadlines:
        for estate in estates:
            tracking = ReportSubmissionTracking.objects.filter(
                deadline=deadline,
                estate=estate,
            ).first()

            now = timezone.now()

            if tracking and tracking.status in (
                ReportSubmissionTracking.Status.SUBMITTED,
                ReportSubmissionTracking.Status.LATE_SUBMITTED,
            ):
                status = "SUBMITTED"
                can_submit = False
            elif now < deadline.start_at:
                status = "UPCOMING"
                can_submit = False
            elif now >= deadline.end_at:
                status = "EXPIRED"
                can_submit = False
            else:
                status = "PENDING"
                can_submit = True

            total_seconds = (
                deadline.end_at - deadline.start_at
            ).total_seconds()

            elapsed_seconds = (
                now - deadline.start_at
            ).total_seconds()

            time_progress = 0
            if total_seconds > 0:
                time_progress = min(
                    100,
                    max(0, int(elapsed_seconds / total_seconds * 100)),
                )

            rows.append({
                "deadline": deadline,
                "estate": estate,
                "tracking": tracking,
                "status": status,
                "can_submit": can_submit,
                "time_progress": time_progress,
            })

    return render(
        request,
        "estate_verification/report_deadline_dashboard.html",
        {"rows": rows},
    )