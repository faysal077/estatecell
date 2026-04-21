from django.db import models
from lands.models import Land
from django.contrib.auth.models import User


def document_path(instance, filename):
    # Use land_{id} for consistent path structure
    return f"land_{instance.land.id}/documents/{filename}"


class Document(models.Model):

    DOCUMENT_TYPES = [
        ('Uncategorized', 'Uncategorized'),
        ('Gazette', 'Gazette'),
        ('Deed (Sale Deed / Registry Deed)', 'Deed (Sale Deed / Registry Deed)'),
        ('Khatiyan', 'Khatiyan'),
        ('Mutation (Namjari)', 'Mutation (Namjari)'),
        ('Lease Deed', 'Lease Deed'),
        ('Land Tax (Khajna / DCR)', 'Land Tax (Khajna / DCR)'),
        ('Porcha', 'Porcha'),
        ('Mouza Map', 'Mouza Map'),
        ('Baina / Agreement for Sale', 'Baina / Agreement for Sale'),
        ('Land Survey Report', 'Land Survey Report'),
        ('Building Plan Approval', 'Building Plan Approval'),
    ]

    SURVEY_TYPES = [
        ('CS', 'CS'),
        ('SA', 'SA'),
        ('RS', 'RS'),
        ('BDS', 'BDS'),
    ]

    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    survey_type = models.CharField(max_length=10, choices=SURVEY_TYPES, blank=True, null=True)
    from_page = models.PositiveIntegerField(blank=True, null=True)
    to_page = models.PositiveIntegerField(blank=True, null=True)

    # Auto incremental doc number (integer)
    document_number = models.IntegerField(unique=True, editable=False, null=True, blank=True)

    issue_date = models.DateField(auto_now_add=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)

    description = models.CharField(max_length=255, blank=True, null=True)
    scanned_copy = models.FileField(upload_to=document_path, blank=True, null=True)

    verified = models.BooleanField(default=False)

    # Merged PDF holding all pages for this document
    merged_pdf = models.FileField(upload_to=document_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.document_type} - {self.document_number}"

    def save(self, *args, **kwargs):
        # Auto increment document_number
        if self.document_number is None:
            last_doc = Document.objects.order_by('-document_number').first()
            self.document_number = 1 if not last_doc else last_doc.document_number + 1

        super().save(*args, **kwargs)

    def get_page_count(self):
        return self.pages.count()

    def get_tags(self):
        """Return all unique tags for this document's pages."""
        return Tag.objects.filter(document_page__document=self).distinct()


class DocumentPage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pages')
    page_number = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to=document_path)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number']

    def __str__(self):
        return f"{self.document} - Page {self.page_number}"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class DocumentTag(models.Model):
    """Association between a Document and a Tag."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='document_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='document_tags')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document', 'tag')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document} - {self.tag.name}"


class PageTag(models.Model):
    """Association between a DocumentPage and a Tag."""
    document_page = models.ForeignKey(DocumentPage, on_delete=models.CASCADE, related_name='page_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='page_tags')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document_page', 'tag')

    def __str__(self):
        return f"{self.document_page} - {self.tag.name}"


class DocumentIndex(models.Model):
    """Index entries for a document - title and page mappings for navigation."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='index_entries')
    title = models.CharField(max_length=255)
    page_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number']

    def __str__(self):
        return f"{self.title} - Page {self.page_number}"
