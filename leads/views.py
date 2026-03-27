from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Lead, LeadActivity, LeadAssignmentHistory
from .forms import LeadForm, LeadActivityForm

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from properties.models import Project
from core.models import ApplicationCode

User = get_user_model()

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'

    def get_queryset(self):
        # Return empty queryset for initial load to improve performance
        # Data is loaded via AJAX call to lead_list_api
        return Lead.objects.none()

class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = 'leads/lead_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = self.object.activities.all()
        context['assignment_history'] = self.object.assignment_history.all()
        context['activity_form'] = LeadActivityForm()
        return context

from django.db.models import Count

class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    success_url = reverse_lazy('lead_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        lead = self.object
        lead.created_by = self.request.user
        lead.updated_by = self.request.user
        
        # Auto-assign if not assigned
        if not lead.assigned_to:
            interested_location = lead.interested_location
            if interested_location:
                # Find user in branch with least leads
                # Case-insensitive match for branch
                user_with_least_leads = User.objects.filter(
                    is_active=True,
                    employee_profile__branch__iexact=interested_location
                ).annotate(
                    lead_count=Count('leads')
                ).order_by('lead_count').first()
                
                if user_with_least_leads:
                    lead.assigned_to = user_with_least_leads
            
            # Fallback: if no location match or no user found, maybe fallback to global least leads?
            # User request was specific about branch matching. I'll keep the global fallback if no location provided?
            # "when new lead is created, assign to user in branch with least number of leads in that interested_location."
            # If no interested_location, I will skip assignment to avoid wrong assignment.
        
        lead.save()
        
        # Determine description based on notes
        description = 'New Lead created.'
        if lead.notes:
            description = f'New Lead created. Note: {lead.notes}'
        
        # Create Lead Activity
        LeadActivity.objects.create(
            lead=lead,
            activity_type='NEW',
            description=description,
            created_by=self.request.user
        )

        # Create Assignment History if assigned
        if lead.assigned_to:
            LeadAssignmentHistory.objects.create(
                lead=lead,
                assigned_by=self.request.user,
                assigned_to=lead.assigned_to,
                is_current=True
            )
            
        return super(CreateView, self).form_valid(form)

class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    success_url = reverse_lazy('lead_list')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.updated_by = self.request.user
        self.object.save()
        return super().form_valid(form)

from .forms import LeadAssignmentForm

class LeadAssignView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadAssignmentForm
    template_name = 'leads/lead_assign_form.html'
    success_url = reverse_lazy('lead_list')

    def form_valid(self, form):
        old_assigned_to = self.get_object().assigned_to
        
        # Save the form and update basic fields
        self.object = form.save(commit=False)
        self.object.updated_by = self.request.user
        self.object.save()
        
        new_assigned_to = self.object.assigned_to
        
        if old_assigned_to != new_assigned_to:
             # Update previous history to not current
             LeadAssignmentHistory.objects.filter(lead=self.object, is_current=True).update(is_current=False)
             
             LeadAssignmentHistory.objects.create(
                lead=self.object,
                assigned_by=self.request.user,
                assigned_to=new_assigned_to,
                is_current=True
            )
             LeadActivity.objects.create(
                lead=self.object,
                activity_type='STATUS_CHANGE',
                description=f'Reassigned to {new_assigned_to} from {old_assigned_to}',
                created_by=self.request.user
            )
        return redirect(self.success_url)

@login_required
def add_lead_activity(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.lead = lead
            activity.created_by = request.user
            activity.save()

            # Automatically update status to CONTACTED if it's currently NEW
            if lead.status == 'NEW':
                lead.status = 'CONTACTED'
                lead.save()
            
            # If activity is "Confirm Booking", change status to "BOOKED"
            if activity.activity_type == 'SOLD':
                lead.status = 'SOLD'
                lead.save()
                messages.success(request, f"Activity '{activity.get_activity_type_name}' logged. Redirecting to complete booking.")
                return redirect(f"{reverse('booking_create')}?lead={lead.pk}")
            
            messages.success(request, f"Activity '{activity.get_activity_type_name}' logged successfully.")
        else:
            messages.error(request, "Error logging activity. Please check the form data.")
    return redirect('lead_detail', pk=pk)

@login_required
def mark_fake_lead(request, pk):
    if request.method == 'POST':
        from django.http import JsonResponse
        lead = get_object_or_404(Lead, pk=pk)
        lead.status = 'FAKE'
        lead.updated_by = request.user
        lead.save(update_fields=['status', 'updated_by', 'updated_at'])
        LeadActivity.objects.create(
            lead=lead,
            activity_type='STATUS_CHANGE',
            description=f'Lead marked as Fake by {request.user}.',
            created_by=request.user
        )
        return JsonResponse({'success': True, 'message': 'Lead marked as fake.'})
    from django.http import JsonResponse
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

import pandas as pd
from django.contrib import messages

@login_required
def upload_leads(request):
    if request.method == 'POST' and request.FILES.get('lead_file'):
        excel_file = request.FILES['lead_file']
        try:
            df = pd.read_excel(excel_file)
            
            # Check if required columns exist
            required_columns = ['first_name', 'last_name', 'phone']
            print("Columns found:", df.columns)
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messages.error(request, f"Missing required columns: {', '.join(missing_columns)}")
                return redirect('lead_list')

            # Pre-fetch users grouped by branch for Round Robin
            users_by_branch = {}
            all_users = User.objects.filter(is_active=True).select_related('employee_profile')
            for user in all_users:
                # Check if user has employee profile and branch
                if hasattr(user, 'employee_profile') and user.employee_profile.branch:
                    branch = user.employee_profile.branch.strip().upper()
                    if branch not in users_by_branch:
                        users_by_branch[branch] = []
                    users_by_branch[branch].append(user)
            
            # Track round robin index for each branch
            branch_indices = {branch: 0 for branch in users_by_branch}

            success_count = 0
            failed_rows = []

            for index, row in df.iterrows():
                try:
                    # Basic validation
                    if pd.isna(row['first_name']) or pd.isna(row['phone']):
                        row_dict = {}
                        for k, v in row.items():
                            if pd.isna(v):
                                row_dict[k] = ""
                            else:
                                row_dict[k] = str(v)
                        row_dict['Error'] = "Missing required fields (first_name or phone)"
                        failed_rows.append(row_dict)
                        continue
                    
                    # Determine assigned user (Round Robin by Branch)
                    assigned_user = None
                    interested_loc = None
                    
                    # Check for interested_location column
                    if 'interested_location' in df.columns and not pd.isna(row['interested_location']):
                        interested_loc = str(row['interested_location']).strip()
                    
                    if interested_loc:
                        branch_key = interested_loc.upper()
                        if branch_key in users_by_branch:
                            users_list = users_by_branch[branch_key]
                            if users_list:
                                current_idx = branch_indices[branch_key]
                                assigned_user = users_list[current_idx % len(users_list)]
                                branch_indices[branch_key] += 1

                    # Parse created_at if present
                    created_at = None
                    if 'created_at' in df.columns and not pd.isna(row['created_at']):
                        try:
                            created_at = pd.to_datetime(row['created_at'])
                        except:
                            created_at = None

                    # Determine interested project
                    project_obj = None
                    if 'interested_project' in df.columns and not pd.isna(row['interested_project']):
                        proj_name = str(row['interested_project']).strip()
                        # Case-insensitive lookup
                        project_obj = Project.objects.filter(short_name__iexact=proj_name).first()

                    lead = Lead.objects.create(
                        first_name=row['first_name'],
                        last_name=row['last_name'] if not pd.isna(row['last_name']) else '',
                        phone=str(row['phone']),
                        email=row['email'] if 'email' in df.columns and not pd.isna(row['email']) else None,
                        status=row['status'] if 'status' in df.columns and not pd.isna(row['status']) else 'NEW',
                        source=row['source'] if 'source' in df.columns and not pd.isna(row['source']) else '',
                        lead_priority=row['lead_priority'] if 'lead_priority' in df.columns and not pd.isna(row['lead_priority']) else None,
                        interested_location=interested_loc,
                        interested_project=project_obj,
                        notes=row['notes'] if 'notes' in df.columns and not pd.isna(row['notes']) else '',
                        lead_location=row['lead_location'] if 'lead_location' in df.columns and not pd.isna(row['lead_location']) else '', # Save interested location
                        created_at=created_at,
                        assigned_to=assigned_user,
                        created_by=request.user,
                        updated_by=request.user
                    )
                    
                    # Create Lead Activity
                    LeadActivity.objects.create(
                        lead=lead,
                        activity_type='NEW',
                        description='Lead created via Bulk Upload.',
                        created_by=request.user
                    )

                    # Create Assignment History if assigned
                    if assigned_user:
                        LeadAssignmentHistory.objects.create(
                            lead=lead,
                            assigned_by=request.user,
                            assigned_to=assigned_user,
                            is_current=True
                        )
                        
                    success_count += 1
                except Exception as e:
                    # Convert row to dict and ensure all values are JSON serializable (str)
                    row_dict = {}
                    for k, v in row.items():
                        if pd.isna(v):
                            row_dict[k] = ""
                        else:
                            row_dict[k] = str(v)
                            
                    row_dict['Error'] = str(e)
                    failed_rows.append(row_dict)
                    continue
            
            if failed_rows:
                request.session['failed_leads_rows'] = failed_rows
                messages.warning(request, f"Uploaded {success_count} leads. {len(failed_rows)} leads failed.", extra_tags='upload_failure')
            elif success_count > 0:
                messages.success(request, f"Successfully uploaded {success_count} leads.")
            else:
                messages.warning(request, "No valid leads were found in the file.")
                
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return redirect('lead_list')

def download_failed_leads(request):
    failed_rows = request.session.get('failed_leads_rows')
    if not failed_rows:
        messages.error(request, "No failed leads report available.")
        return redirect('lead_list')
    
    df = pd.DataFrame(failed_rows)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=failed_leads_report.xlsx'
    df.to_excel(response, index=False)
    return response

from django.http import HttpResponse

from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

def download_lead_template(request):
    # Create a workbook and select the active worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Leads Template"

    # Define headers
    headers = ['first_name', 'last_name', 'phone', 'email', 'lead_location', 'status', 'source','interested_location', 'interested_project', 'lead_priority', 'created_at','notes']
    ws.append(headers)

    # Add sample data
    sample_data = [
        ['John', 'Doe', '1234567890', 'john@example.com', 'Mumbai', 'NEW', 'Website', 'Ernakulam', 'Project A', 'HOT', '2025-12-09',''],
        ['Jane', 'Smith', '0987654321', 'jane@example.com', 'Qatar', 'CONTACTED', 'Referral', 'Ernakulam', 'Project B', 'COLD', '2025-12-09','']
    ]
    for row in sample_data:
        ws.append(row)

    # Get choices from Lead model
    # status_choices = [choice[0] for choice in Lead.STATUS_CHOICES]
    # priority_choices = [choice[0] for choice in Lead.PRIORITY_CHOICES]
    # Source choices - hardcoded as model doesn't have choices defined
    # source_choices = ['Website', 'Referral', 'Walk-in', 'Social Media', 'Other']

    # Helper to add validation
    def add_validation(column_letter, choices):
        # Excel validation list formula has a length limit (255 chars). 
        # If choices are too long, we might need a separate sheet. 
        # For now, assuming these fit.
        formula = f'"{",".join(choices)}"'
        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        dv.error = 'Your entry is not in the list'
        dv.errorTitle = 'Invalid Entry'
        ws.add_data_validation(dv)
        dv.add(f'{column_letter}2:{column_letter}1000')

    # Apply validations
    # Status is column F (6)
    status_choices = ApplicationCode.objects.filter(key='STATUS_CHOICES',is_active=True,is_delete=False).values_list('code', flat=True)
    add_validation('F', status_choices)
    
    # Source is column G (7)
    source_choices = ApplicationCode.objects.filter(key='SOURCE_CHOICES',is_active=True,is_delete=False).values_list('code', flat=True)
    add_validation('G', source_choices)
    
    # Priority is column J (10)
    priority_choices = ApplicationCode.objects.filter(key='PRIORITY_CHOICES',is_active=True,is_delete=False).values_list('code', flat=True)
    add_validation('J', priority_choices)

    locations = Project.objects.values_list('location', flat=True).distinct()
    location_choices = [loc for loc in locations if loc]
    # Interested Location is column H (8)
    add_validation('H', location_choices)   

    projects = Project.objects.values_list('short_name', flat=True).distinct()
    project_choices = [proj for proj in projects if proj]
    # Interested Project is column I (9)
    add_validation('I', project_choices)
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=lead_upload_template.xlsx'
    
    wb.save(response)
    return response
