from django.db import models
from django.conf import settings
from core.models import BaseModel
from properties.models import Project
from bookings.models import Booking

class ProjectMilestone(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='standard_milestones')
    name = models.CharField(max_length=200)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of total agreement value")

    def __str__(self):
        return f"{self.name} ({self.percentage}%) - {self.project.name}"

    class Meta:
        ordering = ['created_at']

class PaymentMilestone(BaseModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=200, help_text="e.g. Booking Amount, Foundation, First Floor, etc.")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of total amount")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.booking}"

    class Meta:
        ordering = ['created_at']

class Payment(BaseModel):
    PAYMENT_MODES = (
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('ONLINE', 'Online Transfer'),
        ('UPI', 'UPI'),
        ('OTHER', 'Other'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    milestone = models.ForeignKey(PaymentMilestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='ONLINE')
    reference_number = models.CharField(max_length=100, blank=True, help_text="Cheque No / Transaction ID")
    
    bank_name = models.CharField(max_length=200, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments_received')
    attachment = models.FileField(upload_to='payment_receipts/', blank=True, null=True)
    
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"₹{self.amount} - {self.booking}"

    class Meta:
        ordering = ['-payment_date']
