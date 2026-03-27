from django.contrib import admin
from .models import Project, Unit

class UnitInline(admin.TabularInline):
    model = Unit
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'created_at')
    search_fields = ('name', 'location')
    inlines = [UnitInline]

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('project', 'unit_number', 'unit_type', 'status')
    list_filter = ('project', 'status', 'unit_type')
    search_fields = ('unit_number', 'project__name')
