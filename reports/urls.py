from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [

    # ========================================================
    # DEFAULT REPORT
    # ========================================================

    path(
        "",
        views.rd_office_report,
        name="rd_office_report"
    ),


    # ========================================================
    # RD OFFICE / DISTRICT / ESTATE
    # ========================================================

    path(
        "rd-office/<str:rd_office>/",
        views.district_report,
        name="district_report"
    ),

    path(
        "rd-office/<str:rd_office>/district/<str:district>/",
        views.estate_report,
        name="estate_report"
    ),

    path(
        "estate/<int:pk>/",
        views.estate_detail,
        name="estate_detail"
    ),


    # ========================================================
    # BSCIC LAND STATUS
    # ========================================================

    path(
        "industrial-land/",
        views.industrial_land_report,
        name="industrial_land_report"
    ),

    path(
        "non-industrial-land/",
        views.non_industrial_land_report,
        name="non_industrial_land_report"
    ),
    path(
        "admin-verification-status/",
        views.admin_verification_status,
        name="admin_verification_status"
    ),

]