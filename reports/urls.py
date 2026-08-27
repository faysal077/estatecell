from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [

    # RD Office
    path(
        "",
        views.rd_office_report,
        name="rd_office_report"
    ),

    # District
    path(
        "rd-office/<str:rd_office>/",
        views.district_report,
        name="district_report"
    ),

    # Estate
    path(
        "rd-office/<str:rd_office>/district/<str:district>/",
        views.estate_report,
        name="estate_report"
    ),

    # Estate detail
    path(
        "estate/<int:pk>/",
        views.estate_detail,
        name="estate_detail"
    ),
]