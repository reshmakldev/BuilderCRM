from django import forms
from .models import ApplicationCode

class ApplicationCodeForm(forms.ModelForm):
    class Meta:
        model = ApplicationCode
        fields = ['key', 'code', 'name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
