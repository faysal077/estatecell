# lands/urls.py
from django.urls import path
from . import views

app_name = "lands"

urlpatterns = [
    path('', views.land_list, name='land_list'),
    path('add/', views.land_create, name='land_create'),
    path('edit/<int:pk>/', views.land_update, name='land_update'),
    path('delete/<int:pk>/', views.land_delete, name='land_delete'),
    path(
        "verify/admin/<int:pk>/",
        views.verify_land_admin,
        name="verify_admin"
    ),

    path(
        "verify/super-admin/<int:pk>/",
        views.verify_land_super_admin,
        name="verify_super_admin"
    ),
]
