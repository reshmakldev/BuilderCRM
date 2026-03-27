from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .models import Employee, Leave, Attendance, Department
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .forms import EmployeeForm, DepartmentForm

User = get_user_model()

class HRDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'hrms/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_employees'] = Employee.objects.filter(is_active=True).count()
        context['departments'] = Department.objects.filter(is_delete=False).count()
        context['pending_leaves'] = Leave.objects.filter(status='PENDING').count()
        return context

# Department Views
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'hrms/department_list.html'
    context_object_name = 'departments'
    
    def get_queryset(self):
        return Department.objects.filter(is_delete=False)

class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'hrms/department_form.html'
    success_url = reverse_lazy('department_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Department created successfully.')
        return super().form_valid(form)

class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'hrms/department_form.html'
    success_url = reverse_lazy('department_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Department updated successfully.')
        return super().form_valid(form)

def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    department.is_delete = True
    department.is_active = False
    department.save()
    messages.success(request, 'Department deleted successfully.')
    return redirect('department_list')

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'hrms/employee_list.html'
    context_object_name = 'employees'

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hrms/employee_form.html'
    success_url = reverse_lazy('employee_list')
    
    def form_valid(self, form):
        # Check if we need to create a user
        if not form.instance.pk:
            username = form.cleaned_data.get('username')
            if username:
                user = User.objects.create_user(
                    username=username,
                    email=form.cleaned_data.get('email'),
                    password=form.cleaned_data.get('password'),
                    first_name=form.cleaned_data.get('first_name'),
                    last_name=form.cleaned_data.get('last_name'),
                    user_role=form.cleaned_data.get('user_role', 'EMPLOYEE')
                )
                form.instance.user = user
                form.instance.created_by = self.request.user
                form.instance.updated_by = self.request.user
        
        return super().form_valid(form)

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hrms/employee_form.html'
    success_url = reverse_lazy('employee_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Employee updated successfully.')
        return super().form_valid(form)

class LeaveListView(LoginRequiredMixin, ListView):
    model = Leave
    template_name = 'hrms/leave_list.html'
    context_object_name = 'leaves'
    
    def get_queryset(self):
        # If user is superuser or HR, show all. Else show only own leaves.
        # For now, showing all for simplicity, or filter by user if they have an employee profile
        if hasattr(self.request.user, 'employee_profile'):
            return Leave.objects.filter(employee=self.request.user.employee_profile)
        return Leave.objects.none()

class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'hrms/attendance_list.html'
    context_object_name = 'attendance_records'
