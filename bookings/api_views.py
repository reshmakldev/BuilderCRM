from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Booking
from django.urls import reverse

def is_privileged(user):
    """Admin / Manager / superuser / staff can see all bookings."""
    return (
        user.is_superuser or
        user.is_staff or
        getattr(user, 'user_role', None) in ('ADMIN', 'MANAGER')
    )

@login_required
def booking_list_api(request):
    """
    API view for DataTable to load bookings asynchronously
    """
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()
    
    # Base QuerySet — role-aware
    user = request.user
    if is_privileged(user):
        queryset = Booking.objects.select_related('lead', 'project', 'unit', 'sales_executive').all()
    else:
        queryset = Booking.objects.select_related('lead', 'project', 'unit', 'sales_executive').filter(sales_executive=user)

    project_id = request.GET.get('project')
    if project_id:
        queryset = queryset.filter(project_id=project_id)

    # Search Filtering
    if search_value:
        queryset = queryset.filter(
            Q(lead__first_name__icontains=search_value) |
            Q(lead__last_name__icontains=search_value) |
            Q(lead__phone__icontains=search_value) |
            Q(project__name__icontains=search_value) |
            Q(unit__unit_number__icontains=search_value) |
            Q(status__icontains=search_value) |
            Q(sales_executive__username__icontains=search_value)
        )

    # Total records
    total_records = Booking.objects.all().count() if is_privileged(user) else Booking.objects.filter(sales_executive=user).count()
    filtered_records = queryset.count()

    # Column ordering
    # 0: Lead Name, 1: Project & Unit, 2: Booking Date, 3: Value, 4: Executive, 5: Status, 6: Actions
    column_mapping = {
        0: 'lead__first_name',
        1: 'project__name',
        2: 'booking_date',
        3: 'agreement_value', # Closest to deal value
        4: 'sales_executive__username',
        5: 'status',
    }
    
    order_column_index = int(request.GET.get('order[0][column]', 2)) # Default to booking date
    order_dir = request.GET.get('order[0][dir]', 'desc')
    
    order_field = column_mapping.get(order_column_index, 'booking_date')
    if order_dir == 'desc':
        order_field = '-' + order_field
        
    queryset = queryset.order_by(order_field)

    # Slice for pagination
    data = queryset[start:start + length]
    
    response_data = []
    for booking in data:
        update_url = reverse('booking_update', args=[booking.pk])
        detail_url = reverse('booking_detail', args=[booking.pk])
        
        # Name HTML
        name_html = f'''
            <div class="fw-semibold text-dark">{booking.lead.first_name} {booking.lead.last_name if booking.lead.last_name else ""}</div>
            <small class="text-muted">{booking.lead.phone}</small>
        '''
        
        # Project & Unit HTML
        project_name = f'<div class="fw-semibold text-primary mb-1">{booking.project.name}</div>' if booking.project else '<div class="text-muted small">Project Deleted</div>'
        unit_display = f'<div class="small fw-bold text-success"><i class="bx bx-home-alt me-1"></i>{booking.unit.unit_number}</div>' if booking.unit else '<div class="small text-danger"><i class="bx bx-home-alt me-1"></i>Unit N/A</div>'
        project_html = f'<td>{project_name}{unit_display}</td>'
        
        # Status HTML
        status_bg = 'bg-label-secondary'
        if booking.status == 'CONFIRMED': status_bg = 'bg-label-success'
        elif booking.status == 'PENDING': status_bg = 'bg-label-warning'
        elif booking.status == 'CANCELLED': status_bg = 'bg-label-danger'
        
        status_display = dict(Booking.STATUS_CHOICES).get(booking.status, booking.status)
        status_html = f'<span class="badge {status_bg}">{status_display}</span>'
        
        # Actions HTML
        actions_html = f'''
            <div class="text-center">
                <a href="{update_url}" class="btn btn-sm btn-icon text-secondary" title="Edit">
                    <i class="bx bx-edit"></i>
                </a>
                <a href="{detail_url}" class="btn btn-sm btn-icon text-primary" title="View">
                    <i class="bx bx-show"></i>
                </a>
                <button type="button" class="btn btn-sm btn-icon text-danger" title="Delete">
                    <i class="bx bx-trash"></i>
                </button>
            </div>
        '''

        response_data.append([
            name_html,
            f"{project_name}{unit_display}",
            booking.booking_date.strftime('%b %d, %Y') if booking.booking_date else "-",
            f"<span class='fw-bold'>₹{booking.total_price:,.0f}</span>",
            booking.sales_executive.username if booking.sales_executive else "-",
            status_html,
            actions_html
        ])

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': response_data
    })
