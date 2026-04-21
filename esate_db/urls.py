from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from lands.models import Land



def dashboard(request):
    """Render dashboard with context data."""
    from django.shortcuts import render

    total_lands = Land.objects.count()
    total_documents = 0
    pending_verifications = total_lands  # Placeholder
    legal_cases = 0  # Placeholder

    return render(request, 'dashboard.html', {
        'total_lands': total_lands,
        'total_documents': total_documents,
        'pending_verifications': pending_verifications,
        'legal_cases': legal_cases,
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
    lands = Land.objects.filter(district__iexact=query_name).values(
        'id', 'owner_name', 'area', 'district', 'upazila', 'mouza',
        'rd_office', 'division', 'dag_no', 'khatian_no'
    )
    return JsonResponse({'lands': list(lands), 'matched_district': query_name})


urlpatterns = [
    path('admin/', admin.site.urls),

    # Dashboard / Home Page
    path('', dashboard, name='dashboard'),

    # App URLs
    path('accounts/', include('accounts.urls')),
    path('lands/', include('lands.urls')),
    path('documents/', include('documents.urls')),

    # API
    path('api/lands/by-district/<str:district_name>/', lands_by_district, name='lands_by_district'),
    path('api/districts/', district_metadata, name='district_metadata'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
