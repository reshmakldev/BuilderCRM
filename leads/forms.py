from django import forms
from .models import Lead, LeadActivity
from properties.models import Project
from core.models import ApplicationCode

class LeadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add form-control class to all fields first
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select,)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

        # Get unique locations from Project model
        locations = Project.objects.values_list('location', flat=True).distinct()
        location_choices = [('', '---------')] + [(loc, loc) for loc in locations if loc]
        self.fields['interested_location'].widget = forms.Select(choices=location_choices, attrs={'class': 'form-select'})

        # Get unique status from ApplicationCode model
        status_choices = list(ApplicationCode.objects.filter(key='STATUS_CHOICES', is_active=True, is_delete=False).values_list('code', 'name'))
        self.fields['status'].widget = forms.Select(choices=status_choices, attrs={'class': 'form-select'})

        # Get unique priority from ApplicationCode model
        priority_choices = list(ApplicationCode.objects.filter(key='PRIORITY_CHOICES', is_active=True, is_delete=False).values_list('code', 'name'))
        self.fields['lead_priority'].widget = forms.Select(choices=[('', '---------')] + priority_choices, attrs={'class': 'form-select'})

        # Get unique source from ApplicationCode model
        source_choices = list(ApplicationCode.objects.filter(key='SOURCE_CHOICES', is_active=True, is_delete=False).values_list('code', 'name'))
        self.fields['source'].widget = forms.Select(choices=[('', '---------')] + source_choices, attrs={'class': 'form-select'})


    class Meta:
        model = Lead
        fields = ['first_name', 'last_name', 'email', 'phone', 'lead_location', 'status', 'lead_priority', 'source', 'assigned_to',
        'interested_project', 'interested_unit', 'interested_location', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class LeadActivityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get activity type choices from ApplicationCode model
        activity_choices = list(ApplicationCode.objects.filter(
            key='ACTIVITY_TYPES', 
            is_active=True, 
            is_delete=False
        ).values_list('code', 'name'))
        self.fields['activity_type'].widget = forms.Select(choices=activity_choices, attrs={'class': 'form-select'})

    class Meta:
        model = LeadActivity
        fields = ['activity_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter activity details...'}),
        }

class LeadAssignmentForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['assigned_to']
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }
