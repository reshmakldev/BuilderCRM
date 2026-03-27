from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Lead

from django.urls import reverse


def is_privileged(user):
    """Admin / Manager / superuser / staff can see all leads."""
    return (
        user.is_superuser or
        user.is_staff or
        getattr(user, 'user_role', None) in ('ADMIN', 'MANAGER')
    )

@login_required
def lead_list_api(request):
    """
    API view for DataTable to load leads asynchronously
    """
    # Helper to clean and validate standard datatable parameters
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()
    
    # Base QuerySet — role-aware
    user = request.user
    if is_privileged(user):
        queryset = Lead.objects.select_related('interested_project', 'interested_unit', 'assigned_to').all()
    else:
        queryset = Lead.objects.select_related('interested_project', 'interested_unit', 'assigned_to').filter(assigned_to=user)

    # Search Filtering
    if search_value:
        queryset = queryset.filter(
            Q(first_name__icontains=search_value) |
            Q(last_name__icontains=search_value) |
            Q(lead_code__icontains=search_value) |
            Q(email__icontains=search_value) |
            Q(phone__icontains=search_value) |
            Q(status__icontains=search_value) |
            Q(interested_project__name__icontains=search_value) |
            Q(interested_unit__unit_number__icontains=search_value) |
            Q(assigned_to__username__icontains=search_value)
        )

    # Total records before filtering — scoped to role
    total_records = Lead.objects.all().count() if is_privileged(user) else Lead.objects.filter(assigned_to=user).count()
    
    # Filtered records count
    filtered_records = queryset.count()

    # Column ordering
    # Map column index from datatable to model field
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_dir = request.GET.get('order[0][dir]', 'desc')
    
    # Maps datatable logic indexes to fields
    # 0: Name (first_name), 1: Status, 2: Phone, 3: Location, 4: Project, 5: Source, 6: Assigned, 7: Created, 8: Actions
    column_mapping = {
        0: 'first_name',
        1: 'status',
        2: 'phone',
        3: 'interested_location',
        4: 'interested_project__name',
        5: 'source',
        6: 'assigned_to__username',
        7: 'created_at',
    }
    
    order_field = column_mapping.get(order_column_index, 'created_at')
    if order_dir == 'desc':
        order_field = '-' + order_field
        
    queryset = queryset.order_by(order_field)

    # Slice for pagination
    data = queryset[start:start + length]
    
    # Format data for JSON response
    response_data = []
    for lead in data:
        # URLs
        detail_url = reverse('lead_detail', args=[lead.pk])
        update_url = reverse('lead_update', args=[lead.pk])
        assign_url = reverse('lead_assign', args=[lead.pk])
        
        # Construct Name HTML (First + Last + Code + Email)
        initials = f"{lead.first_name[0]}{lead.last_name[0] if lead.last_name else ''}".upper()
        name_html = f'''
            <div class="d-flex justify-content-start align-items-center">
                <div class="avatar-wrapper me-3">
                    <div class="avatar avatar-sm bg-label-primary p-2 rounded-circle text-center" 
                         style="width: 32px; height: 32px; line-height: 16px; font-size: 11px; font-weight: 600;">
                        {initials}
                    </div>
                </div>
                <div class="d-flex flex-column">
                    <div class="fw-bold">
                        <a href="{detail_url}" class="text-decoration-none text-dark">
                            {lead.first_name} {lead.last_name if lead.last_name else ""}
                        </a>
                    </div>
                    <div class="small">
                        <span class="text-primary fw-bold text-xs">{lead.lead_code}</span>
                        <span class="mx-1 text-muted">|</span>
                        <a href="#" class="email-link text-muted" data-email="{lead.email if lead.email else ""}">{lead.email if lead.email else ""}</a>
                    </div>
                </div>
            </div>
        '''
        
        # Status Badge HTML
        status_bg = 'bg-label-secondary'
        if lead.status == 'NEW': status_bg = 'bg-label-primary'
        elif lead.status == 'CONTACTED': status_bg = 'bg-label-info'
        elif lead.status == 'QUALIFIED': status_bg = 'bg-label-warning'
        elif lead.status == 'WON' or lead.status == 'SOLD': status_bg = 'bg-label-success'
        elif lead.status == 'LOST': status_bg = 'bg-label-danger'
        elif lead.status == 'FAKE': status_bg = 'bg-label-danger'
        
        status_display = lead.get_status_display()
        status_html = f'<span class="badge {status_bg}">{status_display}</span>'
        
        # Phone Link HTML
        phone_html = f'<a href="#" class="phone-link text-decoration-none" data-phone="{lead.phone}">{lead.phone}</a>'
        
        # Actions HTML
        fake_url = reverse('mark_fake_lead', args=[lead.pk])
        fake_btn = '' if lead.status == 'FAKE' or lead.status == 'SOLD'  else f'''
            <button type="button" class="btn btn-sm btn-icon text-danger mark-fake-btn"
                data-pk="{lead.pk}" data-url="{fake_url}" title="Mark as Fake">
                <i class="bx bx-ghost"></i>
            </button>'''
        actions_html = f'''
            <a href="{update_url}" class="btn btn-sm btn-icon text-secondary" title="Edit">
                <i class="bx bx-edit"></i>
            </a>
            <a href="{assign_url}" class="btn btn-sm btn-icon text-info" title="Assign">
                <i class="bx bx-user-check"></i>
            </a>
            <a href="{detail_url}" class="btn btn-sm btn-icon text-primary" title="View">
                <i class="bx bx-show"></i>
            </a>
            {fake_btn}
        '''
        
        # Construct Project HTML (Project Pin + Name + Unit if Booked)
        project_name = lead.interested_project.name if lead.interested_project else "-"
        unit_display = ""
        if lead.status == 'SOLD':
            booked_unit = lead.bookings.first().unit if lead.bookings.exists() else lead.interested_unit
            if booked_unit:
                unit_display = f'<div class="small fw-bold text-success"><i class="bx bx-home-alt me-1"></i>{booked_unit.unit_number}</div>'
            else:
                unit_display = f'<div class="small text-muted">Unit N/A</div>'
        elif lead.interested_unit:
             unit_display = f'<div class="small text-muted"><i class="bx bx-home me-1"></i>{lead.interested_unit.unit_number}</div>'
        
        project_html = f'<div>{project_name}</div>{unit_display}'

        # Source Badge HTML
        source_bg = 'bg-label-secondary'
        source_val = lead.source.upper() if lead.source else ""
        if 'FACEBOOK' in source_val: source_bg = 'bg-label-primary'
        elif 'WALK' in source_val: source_bg = 'bg-label-info'
        elif 'DIRECT' in source_val: source_bg = 'bg-label-success'
        elif 'INSTA' in source_val: source_bg = 'bg-label-danger'
        elif 'REFER' in source_val: source_bg = 'bg-label-warning'
        
        source_display = lead.get_source_display() if lead.source else "-"
        source_html = f'<span class="badge {source_bg}">{source_display}</span>'

        response_data.append([
            name_html,
            status_html,
            phone_html,
            lead.interested_location if lead.interested_location else "-",
            project_html,
            source_html,
            lead.assigned_to.username if lead.assigned_to else "Unassigned",
            lead.created_at.strftime('%b %d, %Y') if lead.created_at else "",
            actions_html
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': response_data
    })
