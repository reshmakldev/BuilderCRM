from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from leads.models import Lead
from properties.models import Project, Unit
from django.db.models import Count
from .models import ApplicationCode
from .forms import ApplicationCodeForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        from django.db.models.functions import TruncMonth
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Determine scope based on role
        privileged = (
            user.is_superuser or
            user.is_staff or
            getattr(user, 'user_role', None) in ('ADMIN', 'MANAGER')
        )

        if privileged:
            lead_qs = Lead.objects.filter(is_delete=False)
        else:
            lead_qs = Lead.objects.filter(assigned_to=user, is_delete=False)

        # Basic Stats
        context['total_leads'] = lead_qs.count()
        context['new_leads'] = lead_qs.filter(status='NEW').count()
        context['new_leads_count'] = context['new_leads']  # alias for welcome card
        context['won_leads'] = lead_qs.filter(status='WON').count()
        context['lost_leads'] = lead_qs.filter(status='LOST').count()
        context['total_projects'] = Project.objects.count()
        context['available_units'] = Unit.objects.filter(status='AVAILABLE').count()
        context['blocked_units'] = Unit.objects.filter(status='BLOCKED').count()
        context['sold_units'] = Unit.objects.filter(status='SOLD').count()
        context['total_units'] = Unit.objects.count()
        
        # Booking Stats
        from bookings.models import Booking
        booking_qs = Booking.objects.all()
        context['total_bookings'] = booking_qs.count()
        context['confirmed_bookings'] = booking_qs.filter(status='CONFIRMED').count()
        
        # Calculate Success Rate (Won Leads / Total Leads)
        context['success_rate'] = (context['won_leads'] / context['total_leads'] * 100) if context['total_leads'] > 0 else 0
        
        context['recent_leads'] = lead_qs.order_by('-created_at')[:5]
        context['is_privileged_user'] = privileged

        # Chart Data: Leads by Status
        status_counts = lead_qs.values('status').annotate(total=Count('status'))
        status_dict = dict(ApplicationCode.objects.filter(key='STATUS_CHOICES', is_active=True).values_list('code', 'name'))
        context['status_labels'] = [status_dict.get(item['status'], item['status']) for item in status_counts]
        context['status_data'] = [item['total'] for item in status_counts]

        # Chart Data: Leads by Source
        source_counts = lead_qs.values('source').annotate(total=Count('source'))
        source_dict = dict(ApplicationCode.objects.filter(key='SOURCE_CHOICES', is_active=True).values_list('code', 'name'))
        context['source_labels'] = [source_dict.get(item['source'], 'Direct') for item in source_counts]
        context['source_data'] = [item['total'] for item in source_counts]

        # Chart Data: Leads by Priority
        priority_counts = lead_qs.values('lead_priority').annotate(total=Count('lead_priority'))
        priority_dict = dict(ApplicationCode.objects.filter(key='PRIORITY_CHOICES', is_active=True).values_list('code', 'name'))
        priority_labels = [priority_dict.get(item['lead_priority'], 'Unknown') for item in priority_counts]
        priority_data = [item['total'] for item in priority_counts]
        context['priority_labels'] = priority_labels
        context['priority_data'] = priority_data
        context['priority_breakdown'] = zip(priority_labels, priority_data)

        # Chart Data: Monthly Trends (Last 6 months)
        monthly_trend = lead_qs.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Count('id')).order_by('month')
        context['monthly_labels'] = [item['month'].strftime('%b %Y') if item['month'] else 'Unknown' for item in monthly_trend][-6:]
        context['monthly_data'] = [item['total'] for item in monthly_trend][-6:]
        
        # Booking Trend
        booking_trend = booking_qs.annotate(month=TruncMonth('created_at')).values('month').annotate(total=Count('id')).order_by('month')
        context['booking_trend_data'] = [item['total'] for item in booking_trend][-6:]
        
        # Unit Inventory Project-wise Summary & Location Filter
        locations = Project.objects.values_list('location', flat=True).distinct()
        context['locations'] = [loc for loc in locations if loc]
        
        location_filter = self.request.GET.get('location')
        context['selected_location'] = location_filter
        
        project_qs = Project.objects.all()
        if location_filter:
            project_qs = project_qs.filter(location=location_filter)
            
        project_inventory = project_qs.annotate(
            available_cnt=Count('units', filter=Q(units__status='AVAILABLE')),
            blocked_cnt=Count('units', filter=Q(units__status='BLOCKED')),
            sold_cnt=Count('units', filter=Q(units__status='SOLD')),
        ).order_by('name')
        
        context['project_names'] = [p.name for p in project_inventory]
        context['project_available'] = [p.available_cnt for p in project_inventory]
        context['project_booked'] = [p.blocked_cnt for p in project_inventory]
        context['project_sold'] = [p.sold_cnt for p in project_inventory]

        return context


class ApplicationCodeListView(LoginRequiredMixin, ListView):
    model = ApplicationCode
    template_name = 'core/application_code_list.html'
    context_object_name = 'codes'

    def get_queryset(self):
        return ApplicationCode.objects.filter(is_delete=False)

class ApplicationCodeCreateView(LoginRequiredMixin, CreateView):
    model = ApplicationCode
    form_class = ApplicationCodeForm
    template_name = 'core/application_code_form.html'
    success_url = reverse_lazy('application_code_list')

class ApplicationCodeUpdateView(LoginRequiredMixin, UpdateView):
    model = ApplicationCode
    form_class = ApplicationCodeForm
    template_name = 'core/application_code_form.html'
    success_url = reverse_lazy('application_code_list')

    def get_queryset(self):
        return ApplicationCode.objects.filter(is_delete=False)

@login_required
def soft_delete_application_code(request, pk):
    code = ApplicationCode.objects.get(pk=pk)
    code.is_delete = True
    code.is_active = False
    code.save()
    messages.success(request, 'Application Code deleted successfully.')
    return redirect('application_code_list')

@login_required
def upload_application_codes(request):
    if request.method == 'POST' and request.FILES.get('code_file'):
        excel_file = request.FILES['code_file']
        try:
            df = pd.read_excel(excel_file)
            
            required_columns = ['code', 'name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(request, f"Missing required columns: {', '.join(missing_columns)}")
                return redirect('application_code_list')

            success_count = 0
            for index, row in df.iterrows():
                try:
                    if pd.isna(row['code']) or pd.isna(row['name']):
                        continue
                    
                    ApplicationCode.objects.update_or_create(
                        code=row['code'],
                        defaults={
                            'key': row['key'] if 'key' in df.columns and not pd.isna(row['key']) else 'COMMON',
                            'name': row['name'],
                            'description': row['description'] if 'description' in df.columns and not pd.isna(row['description']) else '',
                            'is_active': row['is_active'] if 'is_active' in df.columns and not pd.isna(row['is_active']) else True,
                            'is_delete': False
                        }
                    )
                    success_count += 1
                except Exception as e:
                    continue
            
            if success_count > 0:
                messages.success(request, f"Successfully uploaded/updated {success_count} codes.")
            else:
                messages.warning(request, "No valid data found.")
                
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return redirect('application_code_list')

@login_required
def download_code_template(request):
    data = {
        'key': ['COMMON', 'COMMON'],
        'code': ['CODE001', 'CODE002'],
        'name': ['Example Name 1', 'Example Name 2'],
        'description': ['Description 1', 'Description 2'],
        'is_active': [True, False]
    }
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=application_code_template.xlsx'
    df.to_excel(response, index=False)
    return response
