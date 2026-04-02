from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'document_type',
            'description',
            'scanned_copy',
        ]

        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write short description...'
            }),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'scanned_copy': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
