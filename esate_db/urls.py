from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from lands.models import Land
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required 
from django.db.models import Count, Sum 
from django.shortcuts import render

@login_required(login_url='accounts:login')
def dashboard(request):
    """Render dashboard with summary cards and RD office table."""

    # =====================================================
    # Overall Summary Cards
    # =====================================================

    total_estates = Land.objects.count()

    total_land_area = (
        Land.objects.aggregate(total=Sum('total_area'))['total'] or 0
    )

    total_plots = (
        Land.objects.aggregate(total=Sum('total_plots'))['total'] or 0
    )

    allocated_plots = (
        Land.objects.aggregate(total=Sum('allocated_plots'))['total'] or 0
    )

    remaining_plots = (
        Land.objects.aggregate(total=Sum('remaining_plots'))['total'] or 0
    )

    # =====================================================
    # RD Office Wise Summary Table
    # =====================================================

    rd_office_summary = []

    rd_offices = (
        Land.objects
        .values_list('rd_office', flat=True)
        .distinct()
        .order_by('rd_office')
    )

    for office in rd_offices:

        lands = Land.objects.filter(rd_office=office)

        total_estates_office = lands.count()

        total_area_office = (
            lands.aggregate(total=Sum('total_area'))['total'] or 0
        )

        total_plots_office = (
            lands.aggregate(total=Sum('total_plots'))['total'] or 0
        )

        allocated_plots_office = (
            lands.aggregate(total=Sum('allocated_plots'))['total'] or 0
        )

        remaining_plots_office = (
            lands.aggregate(total=Sum('remaining_plots'))['total'] or 0
        )

        # Average tagging percentage for this RD office
        if total_estates_office > 0:

            tagging_percentage = round(
                sum(l.tagging_percentage for l in lands) / total_estates_office,
                1
            )

        else:
            tagging_percentage = 0

        rd_office_summary.append({
            'rd_office': office,
            'total_estates': total_estates_office,
            'total_area': total_area_office,
            'total_plots': total_plots_office,
            'allocated_plots': allocated_plots_office,
            'remaining_plots': remaining_plots_office,
            'tagging_percentage': tagging_percentage,
        })

    # =====================================================
    # Render Dashboard
    # =====================================================

    return render(request, 'dashboard.html', {

        # Card data
        'total_estates': total_estates,
        'total_land_area': total_land_area,
        'total_plots': total_plots,
        'allocated_plots': allocated_plots,
        'remaining_plots': remaining_plots,

        # Table data
        'rd_office_summary': rd_office_summary,
    })


def district_metadata(request):
    """API endpoint to serve district metadata from local JSON."""
    import json, os
    json_path = os.path.join(settings.BASE_DIR, 'data', 'bd-districts.json')
    if os.path.exists(json_path):
        with open(json_path, encoding='utf-8') as f:
            return JsonResponse(json.load(f))
    return JsonResponse({'districts': []})


def lands_by_district(request, district_name):
    """API endpoint to get lands by district, with fuzzy name matching."""
    from esate_db.districts import DISTRICTS

    # Find the canonical district name from bd-districts.json
    canonical = None
    for d in DISTRICTS:
        if (d['name'].lower() == district_name.lower() or
            district_name.lower() in d['name'].lower() or
            d['name'].lower() in district_name.lower()):
            canonical = d['name']
            break

    # Use canonical name for DB query
    query_name = canonical or district_name
    lands = (
        Land.objects
        .filter(district__iexact=query_name)
        .values(
            "id",
            "owner_name",
            "division",
            "district",
            "upazila",
            "rd_office",
            "total_area",
            "total_plots",
            "allocated_plots",
            "remaining_plots",
        )
    )
    return JsonResponse({'lands': list(lands), 'matched_district': query_name})


urlpatterns = [
    path('adnim/', admin.site.urls),
    path(settings.ADMIN_URL.lstrip("/"), admin.site.urls),

    # Default route → redirect to login
    path('', lambda request: redirect('accounts:login')),

    # Dashboard (protected)
    path('dashboard/', dashboard, name='dashboard'),

    # App URLs
    path('accounts/', include('accounts.urls')),
    path('lands/', include('lands.urls')),
    path('documents/', include('documents.urls')),

    # API
    path('api/lands/by-district/<str:district_name>/', lands_by_district, name='lands_by_district'),
    path('api/districts/', district_metadata, name='district_metadata'),

    # Reports
    path("reports/", include("reports.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
