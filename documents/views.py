from django.shortcuts import render, get_object_or_404, redirect
from .models import Document
from .forms import DocumentForm
from lands.models import Land

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Document
from .forms import DocumentForm
from lands.models import Land
import os

@login_required
def document_create(request, land_id):

    land = get_object_or_404(Land, pk=land_id)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            doc = form.save(commit=False)
            doc.land = land
            doc.issued_by = request.user  # MUST be a valid User instance

            # If a file was uploaded
            uploaded_file = request.FILES.get('scanned_copy')
            if uploaded_file:
                # File name and extension extraction
                filename = uploaded_file.name
                name_part, ext = os.path.splitext(filename)

                doc.file_name = name_part
                doc.file_type = ext.replace('.', '')

            doc.save()  # File automatically saved to: media/land_<id>/documents/

            return JsonResponse({'success': True})

        # Form error response
        return JsonResponse({'success': False, 'errors': form.errors})

    # GET request (return modal form)
    form = DocumentForm()
    return render(request, "documents/document_form.html", {"form": form, "land": land})



@login_required
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)

        if form.is_valid():
            doc = form.save(commit=False)

            uploaded_file = request.FILES.get('scanned_copy')
            if uploaded_file:
                filename = uploaded_file.name
                name_part, ext = os.path.splitext(filename)
                doc.file_name = name_part
                doc.file_type = ext.replace('.', '')

            doc.save()

            return JsonResponse({'success': True})

        return JsonResponse({'success': False, 'errors': form.errors})

    form = DocumentForm(instance=document)
    return render(request, "documents/document_form.html", {"form": form, "document": document})


@login_required
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    document.delete()
    return JsonResponse({'success': True})



def document_list(request, land_id):
    land = get_object_or_404(Land, pk=land_id)
    documents = land.documents.all()
    return render(request, "documents/document_list.html", {
        'documents': documents,
        'land': land
    })


def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, "documents/document_detail.html", {
        'document': document
    })
