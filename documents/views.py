import os
import io
import profile
from urllib import request
from .models import DocumentTagEntry
import fitz  # PyMuPDF
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Count
from .models import Document, DocumentPage, Tag, PageTag, DocumentIndex, DocumentTag
from .forms import DocumentForm, TagForm, DocumentIndexForm
from lands.models import Land
from django.core.files.base import ContentFile
from .utils import extract_pages
import re
from accounts.models import UserProfile, UserRole
# ------------------------------------------------------------------
# Document CRUD
# ------------------------------------------------------------------

@login_required
def document_create(request, land_id):
    land = get_object_or_404(Land, pk=land_id)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            doc = form.save(commit=False)
            doc.land = land
            doc.issued_by = request.user

            uploaded_file = request.FILES.get('scanned_copy')
            if uploaded_file:
                filename = uploaded_file.name
                name_part, ext = os.path.splitext(filename)
                doc.file_name = name_part
                doc.file_type = ext.replace('.', '')

            doc.save()
            return JsonResponse({'success': True})

        return JsonResponse({'success': False, 'errors': form.errors})

    form = DocumentForm()
    return render(request, "documents/document_form.html", {"form": form, "land": land})


@login_required
def document_edit(request, pk):
    # document = get_object_or_404(Document, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.role == UserRole.SUPER_ADMIN:
        document = get_object_or_404(
            Document,
            pk=pk
        )
    else:
        document = get_object_or_404(
            Document,
            pk=pk,
            issued_by=request.user
        )

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

@login_required
def document_list(request, land_id):
    land = get_object_or_404(Land, pk=land_id)
    documents = land.documents.prefetch_related('pages', 'index_entries').all()
    return render(request, "documents/document_list.html", {
        'documents': documents,
        'land': land
    })



@login_required
def upload_document(request, land_id):
    land = get_object_or_404(Land, pk=land_id)

    if request.method == 'POST':
        print("FILES:", request.FILES)

        uploaded_file = request.FILES.get('pdf_file')
        if not uploaded_file:
            return JsonResponse({'success': False, 'error': 'No PDF file uploaded.'})

        doc = Document.objects.create(
            land=land,
            document_type='Uncategorized',
            issued_by=request.user,
            scanned_copy=uploaded_file,
            file_name=uploaded_file.name,
            file_type='pdf'
        )

        return JsonResponse({
            'success': True,
            'document_id': doc.id,
            'document_number': doc.document_number,
            'file_name': doc.file_name
        })

    return JsonResponse({'success': False})


@login_required
def update_document(request, pk):
    """Update document metadata, tags, and create tag entry history."""
    
    #document = get_object_or_404(Document, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.role == UserRole.SUPER_ADMIN:
        document = get_object_or_404(
            Document,
            pk=pk
        )
    else:
        document = get_object_or_404(
            Document,
            pk=pk,
            issued_by=request.user
        )
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        survey_type = request.POST.get('survey_type') or None
        from_page = request.POST.get('from_page')
        to_page = request.POST.get('to_page')
        tags_raw = request.POST.get('tags', '')

        # ---------------- VALIDATION ----------------
        if not document_type:
            return JsonResponse({'success': False, 'error': 'Document type is required.'})

        if document_type == 'Land Survey Report' and not survey_type:
            return JsonResponse({'success': False, 'error': 'Survey type is required.'})

        # ---------------- UPDATE DOCUMENT ----------------
        document.document_type = document_type
        document.survey_type = survey_type

        try:
            document.from_page = int(from_page) if from_page else None
            document.to_page = int(to_page) if to_page else None
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid page numbers.'})

        document.save()

        # ---------------- TAG HISTORY ENTRY ----------------
        entry = DocumentTagEntry.objects.create(
            document=document,
            document_type=document_type,
            survey_type=survey_type,
            from_page=document.from_page,
            to_page=document.to_page,
            created_by=request.user
        )
        if (
            document.scanned_copy
            and document.from_page
            and document.to_page
        ):

            pdf_bytes = extract_pages(
                document.scanned_copy.path,
                document.from_page,
                document.to_page
            )

            safe_name = re.sub(
                r'[^A-Za-z0-9_-]',
                '_',
                document_type
            )

            filename = f"{safe_name}.pdf"

            entry.separated_pdf.save(
                filename,
                ContentFile(pdf_bytes),
                save=True
            )

        # ---------------- TAG PROCESSING ----------------
        tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]

        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            entry.tags.add(tag)

        # ---------------- INDEX GENERATION ----------------
        DocumentIndex.objects.filter(document=document).delete()

        if document.from_page and document.to_page:
            for page in range(document.from_page, document.to_page + 1):
                DocumentIndex.objects.create(
                    document=document,
                    title=f"{document.document_type} Page {page}",
                    page_number=page
                )

        # ---------------- BUILD RESPONSE (IMPORTANT) ----------------
        entries_data = []
        entries = document.tag_entries.prefetch_related('tags').all()

        for e in entries:
            entries_data.append({
                "id": e.id,
                "document_type": e.document_type,
                "from_page": e.from_page,
                "to_page": e.to_page,
                "tags": [t.name for t in e.tags.all()]
            })

        return JsonResponse({
            'success': True,
            'entries': entries_data
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    pages = document.pages.prefetch_related('page_tags__tag').all().order_by('page_number')
    tag_form = TagForm()
    return render(request, "documents/document_detail.html", {
        'document': document,
        'pages': pages,
        'tag_form': tag_form,
    })


# ------------------------------------------------------------------
# Page Management
# ------------------------------------------------------------------

@login_required
def document_add_pages(request, pk):
    """Handle multi-file page upload with tags for a document."""
    document = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if not files:
            return JsonResponse({'success': False, 'errors': 'No files uploaded.'})

        # Parse comma-separated tags
        raw_tags = request.POST.get('tags', '')
        tag_names = [t.strip() for t in raw_tags.split(',') if t.strip()]
        tags = []
        for name in tag_names:
            tags.append(Tag.objects.get_or_create(name=name)[0])

        next_page = document.pages.count() + 1

        for f in files:
            filename = f.name
            name_part, ext = os.path.splitext(filename)
            file_type = ext.replace('.', '').lower()

            page = DocumentPage.objects.create(
                document=document,
                page_number=next_page,
                file=f,
                file_name=name_part,
                file_type=file_type,
            )

            for tag in tags:
                PageTag.objects.get_or_create(document_page=page, tag=tag)

            next_page += 1

        return JsonResponse({'success': True, 'pages_added': len(files)})

    return redirect('documents:document_detail', pk=pk)


@login_required
def document_merge_pdf(request, pk):
    """Merge all pages of a document into a single PDF and save as merged_pdf."""
    document = get_object_or_404(Document, pk=pk)
    pages = document.pages.all().order_by('page_number')

    if not pages.exists():
        return JsonResponse({'success': False, 'error': 'No pages to merge.'})

    output_buffer = io.BytesIO()

    with fitz.open() as merger:
        for page in pages:
            file_path = page.file.path

            if page.file_type == 'pdf':
                with fitz.open(file_path) as src:
                    merger.insert_pdf(src)
            else:
                # Treat as image
                from PIL import Image
                img = Image.open(file_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PDF')
                img_bytes.seek(0)

                with fitz.open(stream=img_bytes.read(), filetype="pdf") as src:
                    merger.insert_pdf(src)

    merger.save(output_buffer)
    output_buffer.seek(0)

    filename = f"merged_{document.document_number}.pdf"

    if document.merged_pdf:
        old_path = document.merged_pdf.path
        if os.path.exists(old_path):
            os.remove(old_path)

    document.merged_pdf.save(filename, output_buffer, save=False)
    document.save()

    return JsonResponse({'success': True, 'merged_pdf': document.merged_pdf.url})


# ------------------------------------------------------------------
# Page Delete
# ------------------------------------------------------------------

@login_required
def delete_page(request, page_id):
    """Delete a specific page."""
    page = get_object_or_404(DocumentPage, pk=page_id)
    page.delete()
    return JsonResponse({'success': True})


# ------------------------------------------------------------------
# Tag Management
# ------------------------------------------------------------------

@login_required
def tag_page(request, page_id):
    """Add a tag to a specific page."""
    page = get_object_or_404(DocumentPage, pk=page_id)

    if request.method == 'POST':
        tag_name = request.POST.get('tag_name', '').strip()
        if not tag_name:
            return JsonResponse({'success': False, 'error': 'Tag name is required.'})

        tag, _ = Tag.objects.get_or_create(name=tag_name)
        pt, created = PageTag.objects.get_or_create(document_page=page, tag=tag)

        return JsonResponse({'success': True, 'tag': tag.name, 'created': created})

    return JsonResponse({'success': False, 'error': 'Invalid method.'})


@login_required
def untag_page(request, page_id):
    """Remove a tag from a specific page."""
    page = get_object_or_404(DocumentPage, pk=page_id)

    if request.method == 'POST':
        tag_name = request.POST.get('tag_name', '').strip()
        deleted, _ = PageTag.objects.filter(document_page=page, tag__name=tag_name).delete()
        return JsonResponse({'success': True, 'deleted': deleted})

    return JsonResponse({'success': False, 'error': 'Invalid method.'})

# @login_required
# def search_by_tag(request):
#     """Search pages by tag name (keyword search)."""
#     query = request.GET.get('q', '').strip()

#     if not query:
#         return render(request, "documents/tag_search.html", {
#             'query': '',
#             'results': [],
#         })

#     # Find pages matching the tag
#     page_tags = PageTag.objects.filter(
#         tag__name__icontains=query
#     ).select_related('document_page', 'document_page__document', 'document_page__document__land')

#     results = []
#     for pt in page_tags:
#         page = pt.document_page
#         doc = page.document
#         results.append({
#             'page': page,
#             'document': doc,
#             'land': doc.land,
#             'tag': pt.tag,
#         })

#     return render(request, "documents/tag_search.html", {
#         'query': query,
#         'results': results,
#     })


# def tag_cloud(request):
#     """Display all tags with page counts."""
#     tags = Tag.objects.all()
#     return render(request, "documents/tag_cloud.html", {'tags': tags})


@login_required
def get_document_pdf(request, pk):
    """Return the merged PDF URL for a document."""
    document = get_object_or_404(Document, pk=pk)
    if document.merged_pdf:
        return JsonResponse({'success': True, 'pdf_url': document.merged_pdf.url})
    elif document.scanned_copy:
        return JsonResponse({'success': True, 'pdf_url': document.scanned_copy.url})
    return JsonResponse({'success': False, 'error': 'No PDF found.'})

@login_required
def get_document_index(request, pk):
    """Return document metadata (type, pages, file_name, tags) for the index panel."""
    document = get_object_or_404(Document, pk=pk)
    # Gather tags from DocumentTag, ordered by newest first
    # tags = list(document.document_tags.select_related('tag').order_by('-created_at').values_list('tag__name', flat=True))
    entries = document.tag_entries.prefetch_related('tags').all()

    data = []
    for e in entries:
        data.append({
            "id": e.id,
            "document_type": e.document_type,
            "from_page": e.from_page,
            "to_page": e.to_page,
            "tags": [t.name for t in e.tags.all()]
        })
        
    # return JsonResponse({
    #     'success': True,
    #     'document_id': document.id,
    #     'document_type': document.document_type or '',
    #     'file_name': document.file_name or '',
    #     'from_page': document.from_page,
    #     'to_page': document.to_page,
    #     'tags': tags,
    # })
    return JsonResponse({
    'success': True,
    # 'document_id': document.id,
    # 'file_name': document.file_name or '',
    'entries': data
})


@login_required
def save_document_index(request):
    """Save a new index entry for a document via AJAX."""
    if request.method == 'POST':
        doc_id = request.POST.get('document_id')
        title = request.POST.get('title', '').strip()
        page_number = request.POST.get('page_number')

        if not doc_id or not title or not page_number:
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        try:
            page_number = int(page_number)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid page number.'})

        document = get_object_or_404(Document, pk=doc_id)
        entry = DocumentIndex.objects.create(
            document=document,
            title=title,
            page_number=page_number
        )
        return JsonResponse({'success': True, 'entry': {
            'id': entry.id,
            'title': entry.title,
            'page_number': entry.page_number
        }})

    return JsonResponse({'success': False, 'error': 'Invalid method.'})


@login_required
def delete_document_index(request, pk):
    """Delete an index entry."""
    entry = get_object_or_404(DocumentIndex, pk=pk)
    entry.delete()
    return JsonResponse({'success': True})


@login_required
def serve_document_pdf(request, pk):
    from django.http import FileResponse, Http404
    from django.shortcuts import get_object_or_404

    document = get_object_or_404(Document, pk=pk)

    file_field = document.scanned_copy or document.merged_pdf
    if not file_field:
        raise Http404("No PDF found.")

    try:
        response = FileResponse(file_field.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{file_field.name}"'
        return response
    except Exception:
        raise Http404("File not found")
    
##################################
# Tagwise Document Deletion
##################################
@login_required
def delete_tag_entry(request, entry_id):

    # entry = get_object_or_404(
    #     DocumentTagEntry,
    #     pk=entry_id
    # )
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.role == UserRole.SUPER_ADMIN:
        entry = get_object_or_404(
            DocumentTagEntry,
            pk=entry_id
        )
    else:
        entry = get_object_or_404(
            DocumentTagEntry,
            pk=entry_id,
            created_by=request.user
        )

    if entry.separated_pdf:

        pdf_path = entry.separated_pdf.path

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    entry.delete()

    return JsonResponse({
        "success": True
    })

@login_required
def delete_tag_entry(request, entry_id):

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'POST required'
        })

    entry = get_object_or_404(
        DocumentTagEntry,
        pk=entry_id
    )

    # Delete generated PDF if exists
    if entry.separated_pdf:

        if os.path.exists(entry.separated_pdf.path):
            os.remove(entry.separated_pdf.path)

    entry.delete()

    return JsonResponse({
        'success': True
    })