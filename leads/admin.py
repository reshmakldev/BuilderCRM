from django.contrib import admin
from .models import Lead, LeadActivity

class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 1

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'status', 'phone', 'email', 'assigned_to', 'created_at')
    list_filter = ('status', 'assigned_to', 'source')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    inlines = [LeadActivityInline]

@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ('lead', 'activity_type', 'created_by', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('lead__first_name', 'lead__last_name', 'description')
