from django.contrib import admin
from .models import Department, Employee, Leave, Attendance

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department', 'designation', 'date_of_joining')
    list_filter = ('department', 'designation', 'date_of_joining')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type', 'start_date')
    search_fields = ('employee__user__username', 'reason')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'is_present')
    list_filter = ('date', 'is_present')
    search_fields = ('employee__user__username',)
