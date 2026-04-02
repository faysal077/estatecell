from django.db import models
from lands.models import Land
from django.contrib.auth.models import User
from django.db import models
from lands.models import Land
from django.contrib.auth.models import User
# def document_path(instance, filename):
#     # DOCUMENTS WILL BE SAVED TO:
#     #   media/land_<id>/documents/<filename>
#     return f"land_{instance.land.id}/documents/{filename}"
def document_path(instance, filename):
    return f"land_{instance.land.id}/documents/{filename}"
class Document(models.Model):

    DOCUMENT_TYPES = [
        ('Gazette', 'Gazette'),
        ('Deed', 'Deed'),
        ('Khatiyan', 'Khatiyan'),
        ('Mutation', 'Mutation'),
        ('Lease Deed', 'Lease Deed'),
        ('Land Tax', 'Land Tax'),
        ('Other', 'Other'),
    ]

    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)

    # Auto incremental doc number (integer)
    document_number = models.IntegerField(unique=True, editable=False, null=True, blank=True)


    issue_date = models.DateField(auto_now_add=True)        # current date
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)   # logged in admin

    file_name = models.CharField(max_length=255, blank=True, null=True)  # extracted from file
    file_type = models.CharField(max_length=50, blank=True, null=True)   # extracted from file extension

    description = models.CharField(max_length=255, blank=True, null=True)   # SHORT text
    scanned_copy = models.FileField(upload_to='documents/', blank=True, null=True)
    scanned_copy = models.FileField(upload_to=document_path, blank=True, null=True)

    verified = models.BooleanField(default=False)

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


# from django.db import models
# from lands.models import Land
# from django.contrib.auth.models import User
#
# class Document(models.Model):
#
#     DOCUMENT_TYPES = [
#         ('Gazette', 'Gazette'),
#         ('Deed', 'Deed'),
#         ('Khatiyan', 'Khatiyan'),
#         ('Mutation', 'Mutation'),
#         ('Lease Deed', 'Lease Deed'),
#         ('Land Tax', 'Land Tax'),
#         ('Other', 'Other'),
#     ]
#
#     land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name='documents')
#     document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
#
#     # NOT auto-field, Django should not treat it as auto
#     document_number = models.IntegerField(
#         unique=True,
#         null=True,
#         blank=True,
#         editable=False
#     )
#
#     issue_date = models.DateField(auto_now_add=True)
#     issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
#
#     file_name = models.CharField(max_length=255, blank=True, null=True)
#     file_type = models.CharField(max_length=50, blank=True, null=True)
#
#     description = models.CharField(max_length=255, blank=True, null=True)
#     scanned_copy = models.FileField(upload_to='documents/', blank=True, null=True)
#
#     verified = models.BooleanField(default=False)
#
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return f"{self.document_type} - {self.document_number}"
#
#     def save(self, *args, **kwargs):
#         # Auto increment document_number manually
#         if self.document_number is None:
#             last_doc = Document.objects.order_by('-document_number').first()
#             self.document_number = 1 if not last_doc else last_doc.document_number + 1
#
#         super().save(*args, **kwargs)
