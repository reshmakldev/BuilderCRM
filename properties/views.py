from django.views.generic import ListView, DetailView
from .models import Project, Unit

class ProjectListView(ListView):
    model = Project
    template_name = 'properties/project_list.html'
    context_object_name = 'projects'

from payments.forms import ProjectMilestoneForm
from payments.models import ProjectMilestone
from django.shortcuts import redirect

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'properties/project_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = self.object.units.all()
        
        # Prepare units data for heatmap
        import json
        unit_data = [
            {
                'number': u.unit_number,
                'type': u.unit_type,
                'status': u.status,
                'floor': u.floor or 0,
                'floorPlanType': u.floor_plan_type or ''
            } for u in context['units']
        ]
        context['unit_data'] = unit_data
        
        # Prepare project config for script
        project_config = {
            'total_floors': self.object.total_floors or 1,
            'floor_plan_types': self.object.floor_plan_types or []
        }
        context['project_config'] = project_config
        
        context['milestones'] = self.object.standard_milestones.all()
        context['milestone_form'] = ProjectMilestoneForm()
        return context

def add_project_milestone(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        names = request.POST.getlist('name')
        percentages = request.POST.getlist('percentage')
        
        created_count = 0
        for name, percentage in zip(names, percentages):
            if name.strip() and percentage:
                ProjectMilestone.objects.create(
                    project=project,
                    name=name.strip(),
                    percentage=percentage,
                    created_by=request.user,
                    updated_by=request.user
                )
                created_count += 1
        
        if created_count > 0:
            messages.success(request, f"{created_count} milestones added successfully!")
        else:
            messages.error(request, "No valid milestones were provided.")
            
    return redirect('project_detail', pk=pk)

def edit_project_milestone(request, milestone_pk):
    milestone = get_object_or_404(ProjectMilestone, pk=milestone_pk)
    project_id = milestone.project.pk
    if request.method == 'POST':
        form = ProjectMilestoneForm(request.POST, instance=milestone)
        if form.is_valid():
            form.save()
            messages.success(request, "Milestone updated successfully!")
        else:
            messages.error(request, "Error updating milestone.")
    return redirect('project_detail', pk=project_id)

from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from .forms import ProjectForm, UnitForm

from django.contrib.auth.mixins import LoginRequiredMixin

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'properties/project_form.html'
    success_url = reverse_lazy('property_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'properties/project_form.html'
    success_url = reverse_lazy('property_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class UnitCreateView(LoginRequiredMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'properties/unit_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        kwargs['project'] = project
        return kwargs

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        form.instance.project = project
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.kwargs['project_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return context

class UnitUpdateView(LoginRequiredMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'properties/unit_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.object.project
        return kwargs

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.object.project.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context

from django.views.generic.edit import FormView
from django.contrib import messages
from .forms import UnitUploadForm
import openpyxl

class UnitUploadView(LoginRequiredMixin, FormView):
    template_name = 'properties/unit_upload.html'
    form_class = UnitUploadForm

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.kwargs['project_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        return context

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        excel_file = form.cleaned_data['excel_file']
        
        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active
            
            # Skip header row
            rows = sheet.iter_rows(min_row=2, values_only=True)
            
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            for row in rows:
                if not row[0]: # Unit Number is mandatory
                    continue
                    
                unit_number = str(row[0]).strip()
                tower = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                floor = row[2] if len(row) > 2 and row[2] is not None else 0
                floor_plan_type = str(row[3]).strip() if len(row) > 3 and row[3] else ''
                unit_type = str(row[4]).strip().upper() if len(row) > 4 and row[4] else '1BHK'
                size_sqft = row[5] if len(row) > 5 and row[5] is not None else 0
                status = str(row[7]).strip().upper() if len(row) > 7 and row[7] else 'AVAILABLE'
                
                # Check duplication
                unit, created = Unit.objects.get_or_create(
                    project=project,
                    unit_number=unit_number,
                    defaults={
                        'tower': tower,
                        'floor': int(floor) if str(floor).isdigit() else 0,
                        'floor_plan_type': floor_plan_type,
                        'unit_type': unit_type,
                        'size_sqft': int(size_sqft) if str(size_sqft).isdigit() else 0,
                        'status': status,
                        'created_by': self.request.user,
                        'updated_by': self.request.user
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    # Optional: Update existing
                    unit.tower = tower
                    unit.floor = int(floor) if str(floor).isdigit() else unit.floor
                    unit.floor_plan_type = floor_plan_type
                    unit.unit_type = unit_type
                    unit.size_sqft = int(size_sqft) if str(size_sqft).isdigit() else unit.size_sqft
                    unit.status = status
                    unit.updated_by = self.request.user
                    unit.save()
                    updated_count += 1

            messages.success(self.request, f"Processed units: {created_count} created, {updated_count} updated.")
            
        except Exception as e:
            messages.error(self.request, f"Error processing Excel file: {str(e)}")
            return self.form_invalid(form)
            
        return super().form_valid(form)

from django.http import JsonResponse

def unit_list_api(request):
    project_id = request.GET.get('project')
    status = request.GET.get('status')
    
    units = Unit.objects.all()
    if project_id:
        units = units.filter(project_id=project_id)
    
    include_id = request.GET.get('include_id')
    if status:
        from django.db.models import Q
        q_filter = Q(status=status)
        if include_id:
            try:
                q_filter |= Q(id=int(include_id))
            except (ValueError, TypeError):
                pass
        units = units.filter(q_filter)
        
    data = [
        {
            'id': unit.id,
            'unit_number': unit.unit_number,
            'size_sqft': unit.size_sqft,
            'unit_type': unit.unit_type
        } for unit in units
    ]
    return JsonResponse(data, safe=False)
