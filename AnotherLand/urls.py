from django.urls import path
from . import views

app_name = "AnotherLand"

urlpatterns = [

    path(
        "",
        views.another_land_list,
        name="another_land_list"
    ),

    path(
        "add/",
        views.another_land_create,
        name="another_land_create"
    ),

    path(
        "edit/<int:pk>/",
        views.another_land_update,
        name="another_land_update"
    ),

    path(
        "delete/<int:pk>/",
        views.another_land_delete,
        name="another_land_delete"
    ),

    path(
        "verification/<int:pk>/",
        views.another_land_verification,
        name="another_land_verification"
    ),

]