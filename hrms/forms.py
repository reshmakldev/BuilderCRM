from django import forms
from .models import Employee, Department
from django.contrib.auth import get_user_model

User = get_user_model()

from core.models import ApplicationCode

class EmployeeForm(forms.ModelForm):
    # Fields to create a new user account if needed
    username = forms.CharField(max_length=150, required=False, help_text="Required if creating a new user")
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    user_role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    
    class Meta:
        model = Employee
        fields = ['department', 'employee_id', 'designation', 'date_of_joining', 'salary', 'address', 'emergency_contact', 'branch']
        widgets = {
            'date_of_joining': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate branch choices
        branch_choices = ApplicationCode.objects.filter(key='LOCATION_CHOICES', is_active=True, is_delete=False).values_list('code', 'name')
        self.fields['branch'].widget = forms.Select(choices=branch_choices, attrs={'class': 'form-select'})

        # If we have an instance (editing), we don't need user creation fields exept names
        if self.instance.pk:
            self.fields.pop('username')
            self.fields.pop('email')
            # self.fields.pop('first_name') # Allow editing
            # self.fields.pop('last_name') # Allow editing
            self.fields.pop('password')
            self.fields.pop('user_role')
            
            # Populate name from User
            if self.instance.user:
                self.fields['first_name'].initial = self.instance.user.first_name
                self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            employee.save()
            
        # Update User name if instance exists and fields are present
        if self.instance.pk and self.instance.user:
            user = self.instance.user
            user.first_name = self.cleaned_data.get('first_name', user.first_name)
            user.last_name = self.cleaned_data.get('last_name', user.last_name)
            user.save()
            
        return employee

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
