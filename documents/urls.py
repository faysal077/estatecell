from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [

    # =========================================================
    # NORMAL LAND DOCUMENTS
    # =========================================================

    path(
        '<int:land_id>/add/',
        views.document_create,
        name='document_create'
    ),

    path(
        '<int:land_id>/list/',
        views.document_list,
        name='document_list'
    ),

    path(
        '<int:land_id>/upload/',
        views.upload_document,
        name='upload_document'
    ),


    # =========================================================
    # ANOTHER LAND DOCUMENTS
    # =========================================================

    path(
        'another-land/<int:another_land_id>/list/',
        views.another_land_document_list,
        name='another_land_document_list'
    ),

    path(
        'another-land/<int:another_land_id>/upload/',
        views.another_land_upload_document,
        name='another_land_upload_document'
    ),


    # =========================================================
    # DOCUMENT CRUD
    # =========================================================

    path(
        'view/<int:pk>/',
        views.document_detail,
        name='document_detail'
    ),

    path(
        'edit/<int:pk>/',
        views.document_edit,
        name='document_edit'
    ),

    path(
        'delete/<int:pk>/',
        views.document_delete,
        name='document_delete'
    ),


    # =========================================================
    # PAGE MANAGEMENT
    # =========================================================

    path(
        '<int:pk>/pages/add/',
        views.document_add_pages,
        name='document_add_pages'
    ),

    path(
        '<int:pk>/merge/',
        views.document_merge_pdf,
        name='document_merge_pdf'
    ),


    # =========================================================
    # PAGE TAGGING
    # =========================================================

    path(
        'page/<int:page_id>/tag/',
        views.tag_page,
        name='tag_page'
    ),

    path(
        'page/<int:page_id>/untag/',
        views.untag_page,
        name='untag_page'
    ),

    path(
        'page/<int:page_id>/delete/',
        views.delete_page,
        name='delete_page'
    ),


    # =========================================================
    # DOCUMENT UPDATE
    # =========================================================

    path(
        '<int:pk>/update/',
        views.update_document,
        name='update_document'
    ),


    # =========================================================
    # PDF
    # =========================================================

    path(
        'pdf/<int:pk>/',
        views.get_document_pdf,
        name='get_document_pdf'
    ),

    path(
        'pdf/<int:pk>/serve/',
        views.serve_document_pdf,
        name='serve_document_pdf'
    ),


    # =========================================================
    # DOCUMENT INDEX
    # =========================================================

    path(
        'pdf/<int:pk>/index/',
        views.get_document_index,
        name='get_document_index'
    ),

    path(
        'index/save/',
        views.save_document_index,
        name='save_document_index'
    ),

    path(
        'index/<int:pk>/delete/',
        views.delete_document_index,
        name='delete_document_index'
    ),


    # =========================================================
    # TAG ENTRY DELETE
    # =========================================================

    path(
        'tag-entry/<int:entry_id>/delete/',
        views.delete_tag_entry,
        name='delete_tag_entry'
    ),
]