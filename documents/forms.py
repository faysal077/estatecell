from django import forms
from .models import Document, Tag, DocumentPage, DocumentIndex


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'document_type',
            'survey_type',
            'from_page',
            'to_page',
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
            'survey_type': forms.Select(attrs={'class': 'form-control'}),
            'from_page': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'to_page': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'scanned_copy': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class DocumentIndexForm(forms.ModelForm):
    class Meta:
        model = DocumentIndex
        fields = ['title', 'page_number']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}),
            'page_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tag name',
            }),
        }


class DocumentPageForm(forms.ModelForm):
    class Meta:
        model = DocumentPage
        fields = ['page_number', 'file', 'file_name', 'file_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
