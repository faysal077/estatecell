from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    path('<int:land_id>/add/', views.document_create, name='document_create'),
    path('<int:land_id>/list/', views.document_list, name='document_list'),
    path('view/<int:pk>/', views.document_detail, name='document_detail'),
    path('edit/<int:pk>/', views.document_edit, name='document_edit'),
    path('delete/<int:pk>/', views.document_delete, name='document_delete'),
]

