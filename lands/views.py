# lands/views.py
import profile
from time import timezone
from urllib import request
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from accounts.models import UserProfile, UserRole
from documents.models import DocumentTagEntry
from documents.models import Document
from .models import Land
from .forms import LandForm
from esate_db.districts import DISTRICTS, DIVISION_NAMES
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.models import UserProfile, UserRole
from documents.models import DocumentTagEntry
from .models import Land
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models import LandVerification
from .models import Land


@login_required
def land_list(request):

    REQUIRED_TAGS = [
        "Gazette",
        "Deed (Sale Deed / Registry Deed)",
        "Khatiyan",
        "Mutation (Namjari)",
        "Lease Deed",
        "Land Tax (Khajna / DCR)",
        "Porcha",
        "Mouza Map",
        "Baina / Agreement for Sale",
        "Land Survey Report",
        "Building Plan Approval",
    ]

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if profile.role == UserRole.SUPER_ADMIN:
        lands = (
            Land.objects
            .all()
            .order_by("-created_at")
        )
    else:
        lands = (
            Land.objects
            .filter(created_by=request.user)
            .order_by("-created_at")
        )

    for land in lands:

        uploaded_types = set(

            DocumentTagEntry.objects.filter(
                document__land=land
            ).values_list(
                "document_type",
                flat=True
            ).distinct()

        )

        land.tag_status = []

        completed_count = 0

        for tag in REQUIRED_TAGS:

            is_completed = tag in uploaded_types

            if is_completed:
                completed_count += 1

            land.tag_status.append({

                "name": tag,

                "completed": is_completed,

            })

        land.completed_count = completed_count

        land.pending_count = len(REQUIRED_TAGS) - completed_count

        land.progress = round(
            completed_count * 100 / len(REQUIRED_TAGS),
            1
        )

    return render(
        request,
        "lands/land_list.html",
        {
            "lands": lands,
        },
    )

@login_required
def land_create(request):
    initial = {}
    # Pre-fill district if passed via query param from map
    if request.GET.get('district'):
        initial['district'] = request.GET['district']

    if request.method == "POST":
        form = LandForm(request.POST)
        if form.is_valid():
            land = form.save(commit=False)
            land.created_by = request.user
            land.save()
            messages.success(request, "Land record created successfully!")
            return redirect('lands:land_list')
    else:
        form = LandForm(initial=initial)
    return render(request, 'lands/land_form.html', {
        'form': form,
        'title': 'Add Land',
        'districts_json': DISTRICTS,
        'divisions': DIVISION_NAMES,
    })

@login_required
def land_update(request, pk):
    # land = get_object_or_404(Land, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.role == UserRole.SUPER_ADMIN:
        land = get_object_or_404(
            Land,
            pk=pk
        )
    else:
        land = get_object_or_404(
            Land,
            pk=pk,
            created_by=request.user
        )
    if request.method == "POST":
        form = LandForm(request.POST, instance=land)
        if form.is_valid():
            form.save()
            messages.success(request, "Land record updated successfully!")
            return redirect('lands:land_list')
    else:
        form = LandForm(instance=land)
    return render(request, 'lands/land_form.html', {
        'form': form,
        'title': 'Edit Land',
        'districts_json': DISTRICTS,
        'divisions': DIVISION_NAMES,
    })

@login_required
def land_delete(request, pk):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.role == UserRole.SUPER_ADMIN:
        land = get_object_or_404(
            Land,
            pk=pk
        )
    else:
        land = get_object_or_404(
            Land,
            pk=pk,
            created_by=request.user
        )
    if request.method == "POST":
        land.delete()
        messages.success(request, "Land record deleted successfully!")
        return redirect('lands:land_list')
    return render(request, 'lands/land_confirm_delete.html', {'land': land})

#########
from django.core.paginator import Paginator

# @login_required
# def land_list(request):

#     profile, _ = UserProfile.objects.get_or_create(user=request.user)

#     if profile.role == UserRole.SUPER_ADMIN:
#         lands = list(Land.objects.all()).order_by("-created_at")
#     else:
#         lands = Land.objects.filter(
#             created_by=request.user
#         ).order_by("-created_at")

#     paginator = Paginator(lands, 10)   # 10 records per page

#     page_number = request.GET.get("page")

#     page_obj = paginator.get_page(page_number)

#     return render(
#         request,
#         "lands/land_list.html",
#         {
#             "lands": page_obj,
#             "page_obj": page_obj,
#         },
#     )

@login_required
def verify_land_admin(request, pk):

    land = get_object_or_404(Land, pk=pk)

    verification = land.verification

    verification.admin_verified = True

    verification.admin_verified_by = request.user

    verification.admin_verified_date = timezone.now()

    verification.save()

    return redirect("lands:land_list")
@login_required
def verify_land_super_admin(request, pk):

    land = get_object_or_404(Land, pk=pk)

    verification = land.verification

    verification.super_admin_verified = True

    verification.super_admin_verified_by = request.user

    verification.super_admin_verified_date = timezone.now()

    verification.save()

    return redirect("lands:land_list")

# ------------------------------
#      Admin and SuperAdmin Verification
# ------------------------------
@login_required
def land_verification(request, pk):

    land = get_object_or_404(Land, pk=pk)

    verification, created = LandVerification.objects.get_or_create(
        land=land
    )

    entries = (
        DocumentTagEntry.objects
        .filter(document__land=land)
        .prefetch_related("tags")
        .select_related(
            "document",
            "created_by"
        )
        .order_by("-created_at")
    )

    profile = request.user.userprofile
    

    if request.method == "POST":

        action = request.POST.get("action")

        ###################################
        # ADMIN VERIFY
        ###################################

        if action == "admin":

            if profile.role != UserRole.ADMIN:

                messages.error(
                    request,
                    "Only Admin can verify."
                )

            else:

                verification.admin_verified = True

                verification.admin_verified_by = request.user

                verification.admin_verified_date = timezone.now()

                verification.save()

                messages.success(
                    request,
                    "Successfully verified."
                )

        ###################################
        # SUPER ADMIN VERIFY
        ###################################

        elif action == "super":

            if profile.role != UserRole.SUPER_ADMIN:

                messages.error(
                    request,
                    "Only Super Admin can verify."
                )

            elif not verification.admin_verified:

                messages.error(
                    request,
                    "Admin verification required."
                )

            else:

                verification.super_admin_verified = True

                verification.super_admin_verified_by = request.user

                verification.super_admin_verified_date = timezone.now()

                verification.save()

                messages.success(
                    request,
                    "Super Admin verification completed."
                )

        return redirect(
            "lands:land_verification",
            pk=pk
        )

    context = {
        "land": land,
        "verification": verification,
        "entries": entries,
        "profile": profile,

        "is_admin": profile.role == UserRole.ADMIN,
        "is_super_admin": profile.role == UserRole.SUPER_ADMIN,
        
    }
    print("Verification context:", context)  # Debugging line

    return render(
        request,
        "lands/admin_verification.html",
        context
    )