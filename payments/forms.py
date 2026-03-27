from django import forms
from .models import PaymentMilestone, Payment, ProjectMilestone

class ProjectMilestoneForm(forms.ModelForm):
    class Meta:
        model = ProjectMilestone
        fields = ['name', 'percentage']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Booking Amount'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class PaymentMilestoneForm(forms.ModelForm):
    class Meta:
        model = PaymentMilestone
        fields = ['name', 'percentage', 'amount', 'due_date', 'is_paid']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Booking Amount'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['milestone', 'percentage', 'amount', 'payment_date', 'payment_mode', 'reference_number', 'bank_name', 'notes', 'attachment']
        labels = {
            'percentage': 'Percentage (%)'
        }
        widgets = {
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cheque No / Transaction ID'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'milestone': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        booking = kwargs.pop('booking', None)
        super().__init__(*args, **kwargs)
        if booking:
            queryset = PaymentMilestone.objects.filter(booking=booking, is_paid=False)
            self.fields['milestone'].queryset = queryset
            self.fields['milestone'].label_from_instance = lambda obj: f"{obj.name} ({obj.percentage}%)"
