from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),

    # Dashboard / Home Page
    path('', TemplateView.as_view(template_name="dashboard.html"), name='dashboard'),

    # App URLs
    path('accounts/', include('accounts.urls')),
    path('lands/', include('lands.urls')),
    path('documents/', include('documents.urls')),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Media file settings for uploaded scanned copies
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
