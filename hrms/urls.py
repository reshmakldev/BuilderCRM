from django.urls import path
from .views import (
    HRDashboardView, EmployeeListView, LeaveListView, AttendanceListView, EmployeeCreateView,
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView, department_delete, EmployeeUpdateView
)

urlpatterns = [
    path('', HRDashboardView.as_view(), name='hr_dashboard'),
    
    # Department URLs
    path('departments/', DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department_update'),
    path('departments/<int:pk>/delete/', department_delete, name='department_delete'),
    
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/add/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/edit/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('leaves/', LeaveListView.as_view(), name='leave_list'),
    path('attendance/', AttendanceListView.as_view(), name='attendance_list'),
]
