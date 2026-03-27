from django import forms
from .models import Project

from core.models import ApplicationCode

class ProjectForm(forms.ModelForm):
    FLOOR_PLAN_CHOICES = [
        ('A', 'Type A'),
        ('B', 'Type B'),
        ('C', 'Type C'),
        ('D', 'Type D'),
        ('E', 'Type E'),
        ('F', 'Type F'),
        ('G', 'Type G'),
        ('H', 'Type H'),
        ('I', 'Type I'),
        ('J', 'Type J'),
        ('K', 'Type K'),
    ]
    floor_plan_types_select = forms.MultipleChoiceField(
        choices=FLOOR_PLAN_CHOICES,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'data-placeholder': 'Select floor plans...'}),
        required=False,
        label="Floor Plan Types"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        location_choices = ApplicationCode.objects.filter(key='LOCATION_CHOICES', is_active=True, is_delete=False).values_list('code', 'name')
        self.fields['location'].widget = forms.Select(choices=location_choices, attrs={'class': 'form-select'})
        
        if self.instance and self.instance.pk and self.instance.floor_plan_types:
            self.fields['floor_plan_types_select'].initial = self.instance.floor_plan_types.split(',')

    def clean(self):
        cleaned_data = super().clean()
        selected_types = cleaned_data.get('floor_plan_types_select')
        if selected_types:
            cleaned_data['floor_plan_types'] = ','.join(selected_types)
        return cleaned_data

    class Meta:
        model = Project
        fields = ['name', 'short_name', 'location', 'number_of_towers', 'total_floors', 'total_apartments', 'floor_plan_types', 'description', 'image', 'brochure']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Name'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short Name'}),
            'number_of_towers': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_floors': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_apartments': forms.NumberInput(attrs={'class': 'form-control'}),
            'floor_plan_types': forms.HiddenInput(), # Hidden, populated by clean
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Project Description'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'brochure': forms.FileInput(attrs={'class': 'form-control'}),
        }

from .models import Unit

class UnitForm(forms.ModelForm):
    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            # Generate Tower choices
            tower_count = project.number_of_towers
            if tower_count > 0:
                tower_choices = [(f"Tower {i}", f"Tower {i}") for i in range(1, tower_count + 1)]
                self.fields['tower'].widget = forms.Select(choices=tower_choices, attrs={'class': 'form-select'})
            
            # Generate Floor choices
            floor_count = project.total_floors
            if floor_count > 0:
                floor_choices = [(i, f"Floor {i}") for i in range(1, floor_count + 1)]
                self.fields['floor'].widget = forms.Select(choices=floor_choices, attrs={'class': 'form-select'})
            
            # Floor Plan Types
            if project.floor_plan_types:
                types = project.floor_plan_types.split(',')
                type_choices = [(t, f"Type {t}") for t in types]
                self.fields['floor_plan_type'].widget = forms.Select(choices=type_choices, attrs={'class': 'form-select'})

    class Meta:
        model = Unit
        fields = ['unit_number', 'tower', 'floor', 'floor_plan_type', 'unit_type', 'size_sqft', 'status', 'floor_plan']
        widgets = {
            'unit_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit Number (e.g., A-101)'}),
            'tower': forms.TextInput(attrs={'class': 'form-control'}), # Fallback
            'floor': forms.NumberInput(attrs={'class': 'form-control'}), # Fallback
            'floor_plan_type': forms.TextInput(attrs={'class': 'form-control'}), # Fallback
            'unit_type': forms.Select(attrs={'class': 'form-select'}),
            'size_sqft': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Size in Sq. Ft.'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'floor_plan': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UnitUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Upload Excel File",
        help_text="Upload an Excel file (.xlsx or .xls) containing unit details.",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx, .xls'})
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            ext = file.name.split('.')[-1].lower()
            if ext not in ['xlsx', 'xls']:
                raise forms.ValidationError("Only Excel files (.xlsx, .xls) are allowed.")
        return file
