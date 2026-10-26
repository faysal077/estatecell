from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import UserProfile, UserRole
from industrial_estate.models import IndustrialEstate
from .forms import EstateOfficerAssignmentForm


def require_super_admin(user):
    if not user.is_authenticated:
        raise PermissionDenied

    if user.is_superuser:
        return

    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        raise PermissionDenied

    if profile.role != UserRole.SUPER_ADMIN:
        raise PermissionDenied


@login_required
def dashboard(request):
    require_super_admin(request.user)

    district_id = request.GET.get("district", "").strip()

    estates = IndustrialEstate.objects.all().select_related(
        "district"
    ).order_by("district__name", "name")

    # Assumes district is a ForeignKey to a model with a name field.
    if district_id:
        if not district_id.isdigit():
            district_id = ""
        else:
            estates = estates.filter(district_id=int(district_id))

    # Get one assignment per estate for display.
    assigned_profiles = UserProfile.objects.filter(
        role=UserRole.ESTATE_OFFICER,
        assigned_estate__isnull=False,
    ).select_related("user", "assigned_estate")

    assigned_by_estate = {
        profile.assigned_estate_id: profile
        for profile in assigned_profiles
    }

    estate_rows = [
        {
            "estate": estate,
            "officer": assigned_by_estate.get(estate.pk),
            "form": EstateOfficerAssignmentForm(
                estate=estate,
                initial={
                    "estate_id": estate.pk,
                    **(
                        {"officer": assigned_by_estate[estate.pk].pk}
                        if estate.pk in assigned_by_estate
                        else {}
                    ),
                },
            ),
        }
        for estate in estates
    ]

    # Build district options from districts actually used by estates.
    districts = (
        IndustrialEstate.objects
        .filter(district__isnull=False)
        .values("district_id", "district__name")
        .distinct()
        .order_by("district__name")
    )

    total_estates = IndustrialEstate.objects.count()
    assigned_estate_ids = set(assigned_by_estate.keys())

    context = {
        "districts": districts,
        "selected_district": district_id,
        "estate_rows": estate_rows,
        "total_estates": total_estates,
        "assigned_count": len(assigned_estate_ids),
        "unassigned_count": max(
            total_estates - len(assigned_estate_ids), 0
        ),
        "available_officer_count": UserProfile.objects.filter(
            role=UserRole.ESTATE_OFFICER,
            user__is_active=True,
            assigned_estate__isnull=True,
        ).count(),
    }

    return render(
        request,
        "estate_assignment/dashboard.html",
        context,
    )


@login_required
@require_POST
def assign_officer(request):
    require_super_admin(request.user)

    estate_id = request.POST.get("estate_id")
    if not estate_id or not estate_id.isdigit():
        messages.error(request, "Invalid estate.")
        return redirect("estate_assignment:dashboard")

    estate = get_object_or_404(
        IndustrialEstate,
        pk=int(estate_id),
    )

    with transaction.atomic():
        # Lock the estate row while validating and saving this assignment.
        estate = IndustrialEstate.objects.select_for_update().get(
            pk=estate.pk
        )

        form = EstateOfficerAssignmentForm(
            request.POST,
            estate=estate,
        )

        if form.is_valid():
            officer = form.cleaned_data["officer"]

            # Lock the officer profile to reduce concurrent assignment races.
            officer = UserProfile.objects.select_for_update().get(
                pk=officer.pk
            )

            # Recheck assignment conditions against current database state.
            if (
                officer.role != UserRole.ESTATE_OFFICER
                or not officer.user.is_active
                or (
                    officer.assigned_estate_id
                    and officer.assigned_estate_id != estate.pk
                )
            ):
                messages.error(
                    request,
                    "The officer is no longer available. Refresh and try again.",
                )
            else:
                duplicate = UserProfile.objects.filter(
                    role=UserRole.ESTATE_OFFICER,
                    assigned_estate=estate,
                ).exclude(pk=officer.pk).exists()

                if duplicate:
                    messages.error(
                        request,
                        "This estate is already assigned to another officer.",
                    )
                else:
                    officer.assigned_estate = estate
                    officer.save(update_fields=["assigned_estate", "updated_at"])

                    messages.success(
                        request,
                        f"{estate.name} has been assigned to "
                        f"{officer.full_name or officer.user.username}.",
                    )
        else:
            messages.error(
                request,
                "Could not assign the officer. Please check the selection.",
            )

    district_id = getattr(estate, "district_id", None)
    if district_id:
        return redirect(
            f"{redirect('estate_assignment:dashboard').url}?district={district_id}"
        )

    return redirect("estate_assignment:dashboard")