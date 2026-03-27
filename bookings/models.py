from django.db import models
from django.conf import settings
from core.models import BaseModel
from leads.models import Lead
from properties.models import Project, Unit

class Booking(BaseModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='bookings')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='bookings')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, related_name='bookings')
    
    booking_date = models.DateField(auto_now_add=True)
    # total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    # booking_amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    
    # payment_plan = models.TextField(blank=True, help_text="Details of payment plan/milestones")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    
    agreement_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    
    # Unit Details (Captured at time of booking)
    area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sqft_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    allotment_number = models.CharField(max_length=100, blank=True, null=True)
    car_parking_number = models.CharField(max_length=100, blank=True, null=True)
    
    sales_executive = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='bookings_as_executive'
    )
    
    notes = models.TextField(blank=True)
    
    # Agreement Value Breakup
    base_cost = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    car_parking_cost = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    statutory_1 = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    statutory_2 = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    gst_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    deposit_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    special_discount = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    agreement_value = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    # Financial details
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    loan_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    loan_status = models.CharField(max_length=50, blank=True, null=True)
    loan_ac_no = models.CharField(max_length=200, blank=True, null=True)
    bank_executive_name = models.CharField(max_length=200, blank=True, null=True)
    bank_executive_contact = models.CharField(max_length=200, blank=True, null=True)   

    @property
    def total_price(self):
        if self.agreement_value and self.agreement_value > 0:
            return self.agreement_value
        area = self.area or (self.unit.size_sqft if self.unit else 0)
        rate = self.sqft_rate or 0
        return area * rate

    @property
    def total_paid(self):
        return self.payments.aggregate(models.Sum('amount'))['amount__sum'] or 0
    
    @property
    def total_paid_percentage(self):
        return self.payments.aggregate(models.Sum('percentage'))['percentage__sum'] or 0

    @property
    def balance(self):
        return self.total_price - self.total_paid

    def __str__(self):
        return f"Booking for {self.lead} - {self.unit}"

    class Meta:
        ordering = ['-created_at']

import os
import re

def booking_document_upload_path(instance, filename):
    project_name = instance.booking.project.name if instance.booking and instance.booking.project else 'Unknown_Project'
    unit_number = str(instance.booking.unit.unit_number) if instance.booking and instance.booking.unit else 'Unknown_Unit'
    
    # Sanitize names for safety in file paths
    project_name = re.sub(r'[^\w\s-]', '', project_name).strip().replace(' ', '_')
    unit_number = re.sub(r'[^\w\s-]', '', unit_number).strip().replace(' ', '_')
    
    return f'booking_docs/{project_name}/{unit_number}/{filename}'

class BookingDocument(BaseModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=booking_document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.booking}"
