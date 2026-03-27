from django.db import models
from core.models import BaseModel

class Project(BaseModel):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    brochure = models.FileField(upload_to='brochures/', blank=True, null=True)
    
    # New Fields
    number_of_towers = models.PositiveIntegerField(default=1, help_text="Number of Towers")
    total_floors = models.PositiveIntegerField(default=1, help_text="Total Floors")
    total_apartments = models.PositiveIntegerField(default=0, help_text="Total Apartments")
    
    # Storing multi-select choices as a comma-separated string
    floor_plan_types = models.CharField(max_length=50, blank=True, help_text="Selected floor plan types")

    def __str__(self):
        return self.name

class Unit(BaseModel):
    UNIT_TYPES = (
        ('1BHK', '1 BHK'),
        ('2BHK', '2 BHK'),
        ('3BHK', '3 BHK'),
        ('4BHK', '4 BHK'),
        ('VILLA', 'Villa'),
        ('DUPLEX', 'Duplex'),
    )
    
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('BLOCKED', 'Blocked'),
        ('SOLD', 'Sold'),
    )
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='units')
    unit_number = models.CharField(max_length=50)
    
    # New Fields
    tower = models.CharField(max_length=50, blank=True, help_text="Tower Number/Name")
    floor = models.PositiveIntegerField(default=0, help_text="Floor Number")
    floor_plan_type = models.CharField(max_length=20, blank=True, help_text="Floor Plan Type (A, B, C, D)")
    
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES, default='1BHK')
    size_sqft = models.PositiveIntegerField(help_text="Size in Square Feet", default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    floor_plan = models.ImageField(upload_to='floor_plans/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.unit_number}"
