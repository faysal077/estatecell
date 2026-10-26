from django.urls import path
from . import views

app_name = "estate_assignment"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "assign/",
        views.assign_officer,
        name="assign_officer",
    ),
]