from django.db import models
from django.conf import settings
from properties.models import Project, Unit
from core.models import BaseModel


def get_status_choices():
    from core.models import ApplicationCode
    return list(
        ApplicationCode.objects.filter(key='STATUS_CHOICES', is_active=True)
        .values_list('code', 'name')
    )
def get_priority_choices():
    from core.models import ApplicationCode
    return list(
        ApplicationCode.objects.filter(key='PRIORITY_CHOICES', is_active=True)
        .values_list('code', 'name')
    )
def get_source_choices():
    from core.models import ApplicationCode
    return list(
        ApplicationCode.objects.filter(key='SOURCE_CHOICES', is_active=True)
        .values_list('code', 'name')
    )

class Lead(BaseModel):
    STATUS_CHOICES = get_status_choices
    
    PRIORITY_CHOICES = get_priority_choices 
    
    SOURCE_CHOICES = get_source_choices

    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=get_status_choices, default='NEW')
    lead_priority = models.CharField(max_length=20, choices=get_priority_choices, blank=True, null=True)
    source = models.CharField(max_length=20, choices=get_source_choices, blank=True, null=True)
    
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    interested_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='interested_leads')
    interested_unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='interested_leads')
    interested_location = models.CharField(max_length=200, blank=True, null=True)
    lead_location = models.CharField(max_length=200, blank=True, null=True)
    
    lead_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if (is_new or not self.lead_code) and self.id:
            generated_code = f"LD{self.id}"
            if self.lead_code != generated_code:
                self.lead_code = generated_code
                super().save(update_fields=['lead_code'])

    def __str__(self):
        return f"{self.lead_code} - {self.first_name} {self.last_name}"

class LeadActivity(BaseModel):
    ACTIVITY_TYPES = (
        ('CALL', 'Call'),
        ('EMAIL', 'Email'),
        ('MEETING', 'Meeting'),
        ('SITE_VISIT', 'Site Visit'),
        ('STATUS_CHANGE', 'Status Change'),
        ('NEW', 'New Lead'),
        ('BOOKED', 'Confirm Booking'),
    )
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='NEW')
    description = models.TextField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_type} - {self.lead}"

    @property
    def get_activity_type_name(self):
        from core.models import ApplicationCode
        code_obj = ApplicationCode.objects.filter(key='ACTIVITY_TYPES', code=self.activity_type).first()
        return code_obj.name if code_obj else self.activity_type

class LeadAssignmentHistory(BaseModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='assignment_history')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments_made')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments_received')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.lead} assigned to {self.assigned_to} by {self.assigned_by}"
