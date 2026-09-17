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
from django.contrib.auth.models import User
from .models import LandVerification
from .models import Land

# lands/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.models import UserProfile, UserRole
from documents.models import DocumentTagEntry
from .models import Land, LandVerification
from .forms import LandForm
from esate_db.districts import DISTRICTS, DIVISION_NAMES

# New view for land verification with admin and super admin checks
from documents.models import DocumentTagEntry

@login_required
def land_list(request):

    # -------------------------------------------------
    # Required Document Tags
    # -------------------------------------------------
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

    # -------------------------------------------------
    # Get logged-in user's profile
    # -------------------------------------------------
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    # =================================================
    # SUPER ADMIN
    # =================================================
    if profile.role == UserRole.SUPER_ADMIN:

        # -------------------------------------------------
        # Get selected filters from URL
        # Example:
        # ?rd_admin=5&estate=17
        # -------------------------------------------------
        selected_rd = request.GET.get("rd_admin", "")
        selected_estate = request.GET.get("estate", "")

        # -------------------------------------------------
        # Base queryset
        # Super Admin can see all lands
        # -------------------------------------------------
        lands = (
            Land.objects
            .all()
            .select_related("created_by")
            .order_by("-created_at")
        )

        # -------------------------------------------------
        # FIRST DROPDOWN
        # Regional Offices / RD Admins
        # -------------------------------------------------
        rd_admins = (
            UserProfile.objects
            .filter(role=UserRole.RD_ADMIN)
            .select_related("user")
            .order_by("user__username")
        )

        # -------------------------------------------------
        # SECOND DROPDOWN
        # Default:
        # Show ALL Data Entry users
        # -------------------------------------------------
        estate_users = (
            User.objects
            .filter(
                userprofile__role=UserRole.DATA_ENTRY
            )
            .select_related("userprofile")
            .order_by("username")
        )

        # -------------------------------------------------
        # If a particular RD Admin is selected
        # -------------------------------------------------
        selected_rd_profile = None

        if selected_rd:

            selected_rd_profile = (
                UserProfile.objects
                .filter(
                    id=selected_rd,
                    role=UserRole.RD_ADMIN
                )
                .select_related("user")
                .first()
            )

            if selected_rd_profile:

                # -----------------------------------------
                # SECOND DROPDOWN:
                # Only Data Entry users under selected RD
                # -----------------------------------------
                estate_users = (
                    User.objects
                    .filter(
                        userprofile__role=UserRole.DATA_ENTRY,
                        userprofile__rd_admin=selected_rd_profile
                    )
                    .select_related("userprofile")
                    .order_by("username")
                )

                # -----------------------------------------
                # LAND RECORDS:
                # Only lands created by those users
                # -----------------------------------------
                lands = lands.filter(
                    created_by__in=estate_users
                )

        # -------------------------------------------------
        # If a particular Estate/Data Entry user is selected
        # -------------------------------------------------
        if selected_estate:

            # Make sure selected estate is actually
            # a Data Entry user
            estate_user = (
                User.objects
                .filter(
                    id=selected_estate,
                    userprofile__role=UserRole.DATA_ENTRY
                )
                .first()
            )

            if estate_user:

                # -----------------------------------------
                # If RD is also selected, make sure the
                # estate belongs to that RD
                # -----------------------------------------
                if selected_rd_profile:

                    if estate_user.userprofile.rd_admin_id != selected_rd_profile.id:
                        # Invalid combination:
                        # selected estate does not belong
                        # to selected RD
                        lands = Land.objects.none()

                    else:
                        lands = lands.filter(
                            created_by=estate_user
                        )

                else:

                    # No RD selected
                    # Filter only by selected estate
                    lands = lands.filter(
                        created_by=estate_user
                    )

        # -------------------------------------------------
        # Context for Super Admin
        # -------------------------------------------------
        context = {
            "lands": lands,

            "rd_admins": rd_admins,
            "estate_users": estate_users,

            "selected_rd": selected_rd,
            "selected_estate": selected_estate,

            "selected_rd_profile": selected_rd_profile,

            "is_superadmin": True,
        }

    # =================================================
    # RD ADMIN
    # =================================================
    elif profile.role == UserRole.RD_ADMIN:

        # -------------------------------------------------
        # Get all Data Entry users under this RD Admin
        # -------------------------------------------------
        data_entry_users = (
            User.objects
            .filter(
                userprofile__role=UserRole.DATA_ENTRY,
                userprofile__rd_admin=profile
            )
        )

        # -------------------------------------------------
        # Get lands created by those Data Entry users
        # -------------------------------------------------
        lands = (
            Land.objects
            .filter(
                created_by__in=data_entry_users
            )
            .select_related("created_by")
            .order_by("-created_at")
        )

        context = {
            "lands": lands,

            "rd_admins": [],
            "estate_users": [],

            "selected_rd": "",
            "selected_estate": "",

            "selected_rd_profile": profile,

            "is_superadmin": False,
        }

    # =================================================
    # DATA ENTRY
    # =================================================
    elif profile.role == UserRole.DATA_ENTRY:

        # -------------------------------------------------
        # Data Entry can only see their own lands
        # -------------------------------------------------
        lands = (
            Land.objects
            .filter(
                created_by=request.user
            )
            .select_related("created_by")
            .order_by("-created_at")
        )

        context = {
            "lands": lands,

            "rd_admins": [],
            "estate_users": [],

            "selected_rd": "",
            "selected_estate": "",

            "selected_rd_profile": profile,

            "is_superadmin": False,
        }

    # =================================================
    # OTHER ROLES
    # =================================================
    else:

        lands = Land.objects.none()

        context = {
            "lands": lands,

            "rd_admins": [],
            "estate_users": [],

            "selected_rd": "",
            "selected_estate": "",

            "selected_rd_profile": None,

            "is_superadmin": False,
        }

    # =================================================
    # Calculate document/tag progress
    # AND CURRENT VERIFICATION STATUS
    # =================================================

    for land in lands:

        # -------------------------------------------------
        # Get verification record
        # -------------------------------------------------
        verification, _ = LandVerification.objects.get_or_create(
            land=land
        )

        # -------------------------------------------------
        # CURRENT VERIFICATION STATUS
        #
        # These methods compare verification date with
        # the latest tagged document/tag entry.
        # -------------------------------------------------
        land.admin_verified_current = (
            verification.is_admin_currently_verified()
        )

        land.super_admin_verified_current = (
            verification.is_super_admin_currently_verified()
        )

        # -------------------------------------------------
        # Uploaded document types
        # -------------------------------------------------
        uploaded_types = set(
            DocumentTagEntry.objects
            .filter(
                document__land=land
            )
            .values_list(
                "document_type",
                flat=True
            )
            .distinct()
        )

        # -------------------------------------------------
        # Tag status
        # -------------------------------------------------
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

        # -------------------------------------------------
        # Progress
        # -------------------------------------------------
        land.completed_count = completed_count

        land.pending_count = (
            len(REQUIRED_TAGS) - completed_count
        )

        land.progress = round(
            completed_count * 100 / len(REQUIRED_TAGS),
            1
        )

    # =================================================
    # Render
    # =================================================

    return render(
        request,
        "lands/land_list.html",
        context
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


@login_required
def land_verification(request, pk):

    # =====================================================
    # GET LAND
    # =====================================================

    land = get_object_or_404(
        Land,
        pk=pk
    )

    # =====================================================
    # GET OR CREATE VERIFICATION RECORD
    # =====================================================

    verification, created = LandVerification.objects.get_or_create(
        land=land
    )

    # =====================================================
    # GET DOCUMENT TAG ENTRIES
    # =====================================================

    entries = (
        DocumentTagEntry.objects
        .filter(
            document__land=land
        )
        .prefetch_related("tags")
        .select_related(
            "document",
            "created_by"
        )
        .order_by("-created_at")
    )

    # =====================================================
    # USER PROFILE
    # =====================================================

    profile = get_object_or_404(
        UserProfile,
        user=request.user
    )

    # =====================================================
    # USER ROLE FLAGS
    # =====================================================

    is_admin = (
        profile.role == UserRole.RD_ADMIN
    )

    is_super_admin = (
        profile.role == UserRole.SUPER_ADMIN
    )

    # =====================================================
    # CURRENT VERIFICATION STATUS
    # =====================================================

    admin_verified_current = (
        verification.is_admin_currently_verified()
    )

    super_admin_verified_current = (
        verification.is_super_admin_currently_verified()
    )

    # =====================================================
    # LATEST TAGGED DOCUMENT
    # =====================================================

    latest_entry = entries.first()

    latest_tagged_date = (
        latest_entry.created_at
        if latest_entry
        else None
    )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        action = request.POST.get("action")

        # =================================================
        # ADMIN VERIFICATION
        # =================================================

        if action == "admin":

            # ---------------------------------------------
            # ONLY RD ADMIN
            # ---------------------------------------------

            if profile.role != UserRole.RD_ADMIN:

                messages.error(
                    request,
                    "Only Regional Admin can verify documents."
                )

                return redirect(
                    "lands:land_verification",
                    pk=pk
                )

            # ---------------------------------------------
            # CHECK TAGGED DOCUMENT
            # ---------------------------------------------

            if not latest_entry:

                messages.error(
                    request,
                    "There are no tagged documents to verify."
                )

                return redirect(
                    "lands:land_verification",
                    pk=pk
                )

            # ---------------------------------------------
            # REQUIRED ADMIN COMMENT
            # ---------------------------------------------

            comment = request.POST.get(
                "admin_verification_comment",
                ""
            ).strip()

            if not comment:

                messages.error(
                    request,
                    "Admin verification comment is required."
                )

                return redirect(
                    "lands:land_verification",
                    pk=pk
                )

            # ---------------------------------------------
            # ADMIN VERIFICATION
            # ---------------------------------------------

            verification.admin_verified = True

            verification.admin_verified_by = request.user

            verification.admin_verified_date = timezone.now()

            verification.admin_verification_comment = comment

            # ---------------------------------------------
            # NEW ADMIN VERIFICATION CREATES A NEW
            # SUPER ADMIN VERIFICATION CYCLE
            # ---------------------------------------------

            verification.super_admin_verified = False

            verification.super_admin_verified_by = None

            verification.super_admin_verified_date = None

            verification.super_admin_verification_comment = ""

            # ---------------------------------------------
            # SAVE
            # ---------------------------------------------

            verification.save(
                update_fields=[
                    "admin_verified",
                    "admin_verified_by",
                    "admin_verified_date",
                    "admin_verification_comment",
                    "super_admin_verified",
                    "super_admin_verified_by",
                    "super_admin_verified_date",
                    "super_admin_verification_comment",
                ]
            )

            messages.success(
                request,
                "Documents successfully verified by Regional Admin."
            )

            return redirect(
                "lands:land_verification",
                pk=pk
            )

        # =================================================
        # SUPER ADMIN VERIFICATION
        # =================================================

        elif action == "super":

            # ---------------------------------------------
            # ONLY SUPER ADMIN
            # ---------------------------------------------

            if profile.role != UserRole.SUPER_ADMIN:

                messages.error(
                    request,
                    "Only Super Admin can perform final verification."
                )

                return redirect(
                    "lands:land_verification",
                    pk=pk
                )

            # ---------------------------------------------
            # ADMIN MUST VERIFY CURRENT DOCUMENTS FIRST
            # ---------------------------------------------

            if not verification.is_admin_currently_verified():

                messages.error(
                    request,
                    "Current documents must be verified by Regional Admin first."
                )

                return redirect(
                    "lands:land_verification",
                    pk=pk
                )

            # ---------------------------------------------
            # REQUIRED SUPER ADMIN COMMENT
            # ---------------------------------------------

            comment = request.POST.get(
                "super_admin_verification_comment",
                ""
            ).strip()

            if not comment:

                messages.error(
                    request,
                    "Super Admin verification comment is required."
                )

                return redirect(
                    "lands:land_verification",
                    pk=pk
                )

            # ---------------------------------------------
            # SUPER ADMIN VERIFICATION
            # ---------------------------------------------

            verification.super_admin_verified = True

            verification.super_admin_verified_by = request.user

            verification.super_admin_verified_date = timezone.now()

            verification.super_admin_verification_comment = comment

            # ---------------------------------------------
            # SAVE
            # ---------------------------------------------

            verification.save(
                update_fields=[
                    "super_admin_verified",
                    "super_admin_verified_by",
                    "super_admin_verified_date",
                    "super_admin_verification_comment",
                ]
            )

            messages.success(
                request,
                "Super Admin final verification completed."
            )

            return redirect(
                "lands:land_verification",
                pk=pk
            )

        # =================================================
        # INVALID ACTION
        # =================================================

        else:

            messages.error(
                request,
                "Invalid verification action."
            )

            return redirect(
                "lands:land_verification",
                pk=pk
            )

    # =====================================================
    # TAGGING PROGRESS
    # =====================================================

    REQUIRED_TAGS = [
        "Gazette",
        "Deed (Sale Deed / Registry Deed)",
        "Khatiyan",
        "Mutation (Namamari)",
        "Lease Deed",
        "Land Tax (Khajna / DCR)",
        "Porcha",
        "Mouza Map",
        "Baina / Agreement for Sale",
        "Land Survey Report",
        "Building Plan Approval",
    ]

    uploaded_types = set(
        DocumentTagEntry.objects
        .filter(
            document__land=land
        )
        .values_list(
            "document_type",
            flat=True
        )
        .distinct()
    )

    completed_tags = sum(
        1
        for tag in REQUIRED_TAGS
        if tag in uploaded_types
    )

    total_required_tags = len(REQUIRED_TAGS)

    pending_tags = (
        total_required_tags -
        completed_tags
    )

    tagging_percentage = (
        round(
            completed_tags * 100 / total_required_tags,
            1
        )
        if total_required_tags
        else 0
    )

    # =====================================================
    # REFRESH VERIFICATION STATUS
    # =====================================================

    admin_verified_current = (
        verification.is_admin_currently_verified()
    )

    super_admin_verified_current = (
        verification.is_super_admin_currently_verified()
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "land": land,

        "verification": verification,

        "entries": entries,

        "profile": profile,

        # ---------------------------------------------
        # ROLE FLAGS REQUIRED BY TEMPLATE
        # ---------------------------------------------

        "is_admin": is_admin,

        "is_super_admin": is_super_admin,

        # ---------------------------------------------
        # VERIFICATION STATUS
        # ---------------------------------------------

        "admin_verified_current": (
            admin_verified_current
        ),

        "super_admin_verified_current": (
            super_admin_verified_current
        ),

        # ---------------------------------------------
        # LATEST TAG
        # ---------------------------------------------

        "latest_entry": latest_entry,

        "latest_tagged_date": latest_tagged_date,

        # ---------------------------------------------
        # TAGGING STATISTICS
        # ---------------------------------------------

        "completed_tags": completed_tags,

        "pending_tags": pending_tags,

        "total_required_tags": total_required_tags,

        "tagging_percentage": tagging_percentage,
    }

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "lands/admin_verification.html",
        context
    )