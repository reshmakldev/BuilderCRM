from django import forms
from .models import Booking, BookingDocument
from properties.models import Unit
from payments.models import Payment
from django.utils import timezone

class BookingForm(forms.ModelForm):
    # Read-only fields for displaying lead information
    lead_code = forms.CharField(required=False, disabled=True, label="Lead Code")
    lead_name = forms.CharField(required=False, disabled=True, label="Lead Name")
    email = forms.EmailField(required=False, disabled=True, label="Email Address")
    phone = forms.CharField(required=False, disabled=True, label="Phone Number")
    lead_status = forms.CharField(required=False, disabled=True, label="Lead Status")
    booking_date = forms.DateField(required=False, disabled=True, label="Booking Date", initial=timezone.now().date())

    # Virtual fields for initial payment
    initial_payment_amount = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label="Initial Payment Amount")
    initial_payment_mode = forms.ChoiceField(
        choices=Payment.PAYMENT_MODES,
        required=False,
        label="Payment Mode"
    )
    initial_payment_reference = forms.CharField(max_length=100, required=False, label="Reference Number")

    class Meta:
        model = Booking
        fields = [
            'lead', 'project', 'unit', 'status',
            'area', 'sqft_rate', 'allotment_number', 'car_parking_number',
            'base_cost', 'car_parking_cost', 'statutory_1', 'statutory_2',
            'gst_amount', 'deposit_amount', 'special_discount', 'agreement_value',
            'sales_executive', 'notes', 'loan_amount', 'loan_status', 'bank_name',
            'loan_ac_no', 'bank_executive_name', 'bank_executive_contact'
        ]
        labels = {
            'base_cost': 'Cost',
            'statutory_1': 'Statutory 1',
            'statutory_2': 'Statutory 2',
            'gst_amount': 'GST',
            'deposit_amount': 'Deposit',
            'special_discount': 'Special Discount',
            'agreement_value': 'Agreement Value',
            'car_parking_cost': 'Car Parking Cost',
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
            'unit': forms.Select(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            new_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = f"{existing_class} {new_class}".strip()
        
        # Populate lead info fields if a lead is present in instance or initial
        lead = None
        if self.instance and hasattr(self.instance, 'lead') and self.instance.lead:
            lead = self.instance.lead
        elif 'lead' in self.initial:
            lead = self.initial['lead']
        
        if lead:
            self.fields['lead_code'].initial = getattr(lead, 'lead_code', '-')
            self.fields['lead_name'].initial = f"{lead.first_name} {lead.last_name}"
            self.fields['email'].initial = lead.email
            self.fields['phone'].initial = lead.phone
            self.fields['lead_status'].initial = lead.get_status_display()

        # Determine project to filter units
        project_id = None
        if 'project' in self.data:
            try:
                project_id = int(self.data.get('project'))
            except (ValueError, TypeError): pass
        elif self.instance and self.instance.pk and self.instance.project_id:
            project_id = self.instance.project_id
        elif 'project' in self.initial:
            project_obj = self.initial.get('project')
            if isinstance(project_obj, int):
                project_id = project_obj
            elif hasattr(project_obj, 'pk'):
                project_id = project_obj.pk

        if project_id:
            from django.db.models import Q
            queryset = Unit.objects.filter(project_id=project_id)
            
            # Allow 'AVAILABLE' units OR the unit already assigned or in initial
            current_unit_id = None
            if self.instance and self.instance.pk and self.instance.unit_id:
                current_unit_id = self.instance.unit_id
            elif 'unit' in self.initial:
                unit_obj = self.initial.get('unit')
                current_unit_id = unit_obj.pk if hasattr(unit_obj, 'pk') else unit_obj
            
            if current_unit_id:
                queryset = queryset.filter(Q(status='AVAILABLE') | Q(id=current_unit_id))
            else:
                queryset = queryset.filter(status='AVAILABLE')
                
            self.fields['unit'].queryset = queryset
        else:
            self.fields['unit'].queryset = Unit.objects.none()

class BookingDocumentForm(forms.ModelForm):
    class Meta:
        model = BookingDocument
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
