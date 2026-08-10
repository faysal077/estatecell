# accounts/urls.py

from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [

    # User Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path( "first-password-change/", views.first_password_change, name="first_password_change" ),

]
