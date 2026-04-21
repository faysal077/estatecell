from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    # Document CRUD
    path('<int:land_id>/add/', views.document_create, name='document_create'),
    path('<int:land_id>/list/', views.document_list, name='document_list'),
    path('view/<int:pk>/', views.document_detail, name='document_detail'),
    path('edit/<int:pk>/', views.document_edit, name='document_edit'),
    path('delete/<int:pk>/', views.document_delete, name='document_delete'),

    # Page management
    path('<int:pk>/pages/add/', views.document_add_pages, name='document_add_pages'),
    path('<int:pk>/merge/', views.document_merge_pdf, name='document_merge_pdf'),

    # Page tagging
    path('page/<int:page_id>/tag/', views.tag_page, name='tag_page'),
    path('page/<int:page_id>/untag/', views.untag_page, name='untag_page'),
    path('page/<int:page_id>/delete/', views.delete_page, name='delete_page'),

    # Tag search
    path('search/', views.search_by_tag, name='search_by_tag'),
    path('tags/', views.tag_cloud, name='tag_cloud'),

    # Document upload with PDF and index
    path('<int:land_id>/upload/', views.upload_document, name='upload_document'),
    path('<int:pk>/update/', views.update_document, name='update_document'),
    path('pdf/<int:pk>/', views.get_document_pdf, name='get_document_pdf'),
]
