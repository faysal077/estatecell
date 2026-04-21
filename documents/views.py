import os
import io

import fitz  # PyMuPDF
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Count

from .models import Document, DocumentPage, Tag, PageTag, DocumentIndex
from .forms import DocumentForm, TagForm, DocumentIndexForm
from lands.models import Land


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
    documents = land.documents.prefetch_related('pages', 'index_entries').all()
    return render(request, "documents/document_list.html", {
        'documents': documents,
        'land': land
    })


# @login_required
# def upload_document(request, land_id):
#     """Handle document upload with PDF, metadata, tags, and index entries."""
#     land = get_object_or_404(Land, pk=land_id)

#     if request.method == 'POST':
#         uploaded_file = request.FILES.get('pdf_file')
#         if not uploaded_file:
#             return JsonResponse({'success': False, 'error': 'No PDF file uploaded.'})

#         document_type = request.POST.get('document_type', '')
#         survey_type = request.POST.get('survey_type') or None
#         from_page = request.POST.get('from_page') or None
#         to_page = request.POST.get('to_page') or None
#         tags_raw = request.POST.get('tags', '')
#         index_entries_raw = request.POST.get('index_entries', '')

#         # Parse page numbers
#         try:
#             from_page = int(from_page) if from_page else None
#             to_page = int(to_page) if to_page else None
#         except ValueError:
#             return JsonResponse({'success': False, 'error': 'Invalid page numbers.'})

#         # Get survey types validation
#         if document_type == 'Land Survey Report' and not survey_type:
#             return JsonResponse({'success': False, 'error': 'Survey type is required for Land Survey Report.'})
# #document_type='Uncategorized',
#         # Create document
#         doc = Document(
#             land=land,
#             document_type='Uncategorized',
#             survey_type=survey_type,
#             from_page=from_page,
#             to_page=to_page,
#             issued_by=request.user,
#         )

#         filename = uploaded_file.name
#         name_part, ext = os.path.splitext(filename)
#         doc.file_name = name_part
#         doc.file_type = ext.replace('.', '').lower()
#         doc.scanned_copy = uploaded_file
#         doc.save()

#         # Parse and create tags
#         tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
#         created_tags = []
#         for name in tag_names:
#             tag, _ = Tag.objects.get_or_create(name=name)
#             created_tags.append(tag)

#         # Parse index entries (format: "title|page, title|page, ...")
#         if index_entries_raw:
#             for entry in index_entries_raw.split(','):
#                 entry = entry.strip()
#                 if '|' in entry:
#                     title, page_str = entry.rsplit('|', 1)
#                     try:
#                         page_num = int(page_str.strip())
#                         DocumentIndex.objects.create(
#                             document=doc,
#                             title=title.strip(),
#                             page_number=page_num
#                         )
#                     except ValueError:
#                         pass

#         return JsonResponse({
#             'success': True,
#             'document_id': doc.id,
#             'document_number': doc.document_number
#         })

#     return JsonResponse({'success': False, 'error': 'Invalid request method.'})


# @login_required
# def update_document(request, pk):
#     """Update document metadata (tags, pages, etc.) after upload."""
#     document = get_object_or_404(Document, pk=pk)

#     if request.method == 'POST':
#         document_type = request.POST.get('document_type')
#         survey_type = request.POST.get('survey_type') or None
#         from_page = request.POST.get('from_page') or None
#         to_page = request.POST.get('to_page') or None
#         tags_raw = request.POST.get('tags', '')

#         if document_type:
#             document.document_type = document_type

#         document.survey_type = survey_type

#         try:
#             document.from_page = int(from_page) if from_page else None
#             document.to_page = int(to_page) if to_page else None
#         except ValueError:
#             pass

#         document.save()

#         # Update tags
#         if tags_raw:
#             tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
#             for name in tag_names:
#                 tag, _ = Tag.objects.get_or_create(name=name)

#         return JsonResponse({'success': True})

#     return JsonResponse({'success': False, 'error': 'Invalid request method.'})

# @login_required
# def upload_document(request, land_id):
#     """Upload only PDF and create a minimal document."""
#     land = get_object_or_404(Land, pk=land_id)

#     if request.method == 'POST':
#         uploaded_file = request.FILES.get('pdf_file')

#         if not uploaded_file:
#             return JsonResponse({'success': False, 'error': 'No PDF file uploaded.'})

#         try:
#             filename = uploaded_file.name
#             name_part, ext = os.path.splitext(filename)

#             doc = Document.objects.create(
#                 land=land,
#                 document_type='Uncategorized',  # temporary
#                 issued_by=request.user,
#                 file_name=name_part,
#                 file_type=ext.replace('.', '').lower(),
#                 scanned_copy=uploaded_file
#             )

#             return JsonResponse({
#                 'success': True,
#                 'document_id': doc.id,
#                 'document_number': doc.document_number
#             })

#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})

#     return JsonResponse({'success': False, 'error': 'Invalid request method.'})

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
            'document_number': doc.document_number
        })

    return JsonResponse({'success': False})

@login_required
def update_document(request, pk):
    """Update document metadata, tags, and auto-create index."""
    document = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        survey_type = request.POST.get('survey_type') or None
        from_page = request.POST.get('from_page')
        to_page = request.POST.get('to_page')
        tags_raw = request.POST.get('tags', '')

        # 🔹 VALIDATION
        if not document_type:
            return JsonResponse({'success': False, 'error': 'Document type is required.'})

        if document_type == 'Land Survey Report' and not survey_type:
            return JsonResponse({'success': False, 'error': 'Survey type is required.'})

        # 🔹 UPDATE DOCUMENT
        document.document_type = document_type
        document.survey_type = survey_type

        try:
            document.from_page = int(from_page) if from_page else None
            document.to_page = int(to_page) if to_page else None
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid page numbers.'})

        document.save()

        # 🔹 TAGS (clean + assign)
        tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]

        # Optional: clear previous tags logic (if you add relation later)

        for name in tag_names:
            Tag.objects.get_or_create(name=name)

        # 🔹 AUTO INDEX CREATION
        DocumentIndex.objects.filter(document=document).delete()

        if document.from_page and document.to_page:
            for page in range(document.from_page, document.to_page + 1):
                DocumentIndex.objects.create(
                    document=document,
                    title=f"{document.document_type} Page {page}",
                    page_number=page
                )

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


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


def search_by_tag(request):
    """Search pages by tag name (keyword search)."""
    query = request.GET.get('q', '').strip()

    if not query:
        return render(request, "documents/tag_search.html", {
            'query': '',
            'results': [],
        })

    # Find pages matching the tag
    page_tags = PageTag.objects.filter(
        tag__name__icontains=query
    ).select_related('document_page', 'document_page__document', 'document_page__document__land')

    results = []
    for pt in page_tags:
        page = pt.document_page
        doc = page.document
        results.append({
            'page': page,
            'document': doc,
            'land': doc.land,
            'tag': pt.tag,
        })

    return render(request, "documents/tag_search.html", {
        'query': query,
        'results': results,
    })


def tag_cloud(request):
    """Display all tags with page counts."""
    tags = Tag.objects.all()
    return render(request, "documents/tag_cloud.html", {'tags': tags})


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
def serve_document_pdf(request, pk):
    """Serve the PDF file directly to avoid URL encoding issues."""
    from django.http import FileResponse, Http404
    document = get_object_or_404(Document, pk=pk)
    if document.scanned_copy:
        try:
            return FileResponse(
                document.scanned_copy.open('rb'),
                content_type='application/pdf',
                as_attachment=False,
                filename=document.scanned_copy.name
            )
        except Exception:
            raise Http404("File not found")
    elif document.merged_pdf:
        try:
            return FileResponse(
                document.merged_pdf.open('rb'),
                content_type='application/pdf',
                as_attachment=False,
                filename=document.merged_pdf.name
            )
        except Exception:
            raise Http404("File not found")
    raise Http404("No PDF found.")
