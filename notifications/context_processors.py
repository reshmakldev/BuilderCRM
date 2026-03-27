from leads.models import Lead


def is_privileged(user):
    """Returns True if the user is admin, manager, superuser or staff."""
    return (
        user.is_superuser or
        user.is_staff or
        getattr(user, 'user_role', None) in ('ADMIN', 'MANAGER')
    )


def notifications_context(request):
    """
    Injects role-aware notification counts into every template context.
    - ADMIN / MANAGER / superuser / staff  → count of ALL new leads
    - Everyone else                         → count of new leads assigned to them
    """
    if request.user.is_authenticated:
        base_qs = Lead.objects.filter(status='NEW', is_delete=False)
        if is_privileged(request.user):
            new_leads_count = base_qs.count()
        else:
            new_leads_count = base_qs.filter(assigned_to=request.user).count()
    else:
        new_leads_count = 0

    return {
        'new_leads_count': new_leads_count,
    }
