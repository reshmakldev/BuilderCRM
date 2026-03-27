from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from leads.models import Lead, LeadAssignmentHistory, LeadActivity
from core.models import ApplicationCode
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Automatically reassigns NEW leads not contacted within the configured period'

    def handle(self, *args, **options):
        # 1. Get reassignment threshold from ApplicationCode Master
        # Expected Key: 'SYSTEM_CONFIG', Code: 'LEAD_REASSIGN_TIMEOUT'
        config = ApplicationCode.objects.filter(key='SYSTEM_CONFIG', code='LEAD_REASSIGN_TIMEOUT').first()
        try:
            days_threshold = int(config.name) if config and config.name.isdigit() else 5
        except (ValueError, TypeError):
            days_threshold = 5
        
        self.stdout.write(f"Using reassignment threshold: {days_threshold} days.")
        
        threshold_date = timezone.now() - timedelta(days=days_threshold)
        
        # 2. Find leads that are still 'NEW' and were assigned more than X days ago
        # We check the latest current assignment record for each lead
        stale_histories = LeadAssignmentHistory.objects.filter(
            is_current=True,
            lead__status='NEW',
            assigned_at__lte=threshold_date,
            lead__is_delete=False
        ).select_related('lead', 'assigned_to')

        if not stale_histories.exists():
            self.stdout.write(self.style.SUCCESS('No leads require reassignment at this time.'))
            return

        # Deduplicate to prevent duplicate reassignments on a single run
        unique_stale_leads = {}
        for history in stale_histories:
            unique_stale_leads[history.lead.id] = history

        self.stdout.write(f"Found {len(unique_stale_leads)} unique stale leads.")

        from django.db import transaction
        
        for lead_id, history in unique_stale_leads.items():
            try:
                with transaction.atomic():
                    # 3. Lock the history record to see if it's already been processed properly by another process
                    locked_history = LeadAssignmentHistory.objects.select_for_update().get(id=history.id)
                    if not locked_history.is_current:
                        self.stdout.write(self.style.WARNING(f"Skipping Lead {lead_id}: Already processed by another worker."))
                        continue
                        
                    lead = locked_history.lead
                    old_user = locked_history.assigned_to
                    
                    # Find another user with the least count of leads
                    new_user = User.objects.filter(
                        is_active=True
                    ).exclude(
                        id=old_user.id if old_user else None
                    ).annotate(
                        lead_count=Count('leads', filter=Q(leads__is_delete=False))
                    ).order_by('lead_count').first()

                    if not new_user:
                        self.stdout.write(self.style.WARNING(f"Skipping Lead {lead.id}: No other active users found."))
                        continue

                    # 4. Perform Reassignment
                    # Update Lead
                    lead.assigned_to = new_user
                    lead.updated_at = timezone.now() # Explicitly update updated_at timestamp to satisfy requirement
                    lead.save()
                    
                    # Update old history safely under lock
                    locked_history.is_current = False
                    locked_history.save()
                    
                    # Create new history
                    LeadAssignmentHistory.objects.create(
                        lead=lead,
                        assigned_to=new_user,
                        assigned_by=None, # System
                        is_current=True
                    )
                    
                    # 5. Create LeadActivity with specific description
                    LeadActivity.objects.create(
                        lead=lead,
                        activity_type='STATUS_CHANGE',
                        description='re-assigned due to delay in contacting',
                        created_by=None # System
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"Lead {lead.id} ({lead.first_name}) reassigned from {old_user} to {new_user}."
                    ))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reassigning lead {lead_id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS('Reassignment process completed.'))
