import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from core.models import ApplicationCode
from django.utils import timezone

now = timezone.now()

codes = [
    # STATUS_CHOICES
    {'key': 'STATUS_CHOICES', 'code': 'NEW', 'name': 'New'},
    {'key': 'STATUS_CHOICES', 'code': 'CONTACTED', 'name': 'Contacted'},
    {'key': 'STATUS_CHOICES', 'code': 'QUALIFIED', 'name': 'Qualified'},
    {'key': 'STATUS_CHOICES', 'code': 'NEGOTIATION', 'name': 'Negotiation'},
    {'key': 'STATUS_CHOICES', 'code': 'WON', 'name': 'Won'},
    {'key': 'STATUS_CHOICES', 'code': 'LOST', 'name': 'Lost'},
    
    # PRIORITY_CHOICES
    {'key': 'PRIORITY_CHOICES', 'code': 'HOT', 'name': 'Hot'},
    {'key': 'PRIORITY_CHOICES', 'code': 'COLD', 'name': 'Cold'},
    {'key': 'PRIORITY_CHOICES', 'code': 'WARM', 'name': 'Warm'},
    {'key': 'PRIORITY_CHOICES', 'code': 'LOST', 'name': 'Lost'},
    
    # ACTIVITY_TYPES
    {'key': 'ACTIVITY_TYPES', 'code': 'CALL', 'name': 'Call'},
    {'key': 'ACTIVITY_TYPES', 'code': 'EMAIL', 'name': 'Email'},
    {'key': 'ACTIVITY_TYPES', 'code': 'MEETING', 'name': 'Meeting'},
    {'key': 'ACTIVITY_TYPES', 'code': 'SITE_VISIT', 'name': 'Site Visit'},
    {'key': 'ACTIVITY_TYPES', 'code': 'STATUS_CHANGE', 'name': 'Status Change'},
    {'key': 'ACTIVITY_TYPES', 'code': 'NEW', 'name': 'New Lead'},

    # SOURCE_CHOICES
    {'key': 'SOURCE_CHOICES', 'code': 'WEBSITE', 'name': 'Website'},
    {'key': 'SOURCE_CHOICES', 'code': 'REFERRAL', 'name': 'Referral'},
    {'key': 'SOURCE_CHOICES', 'code': 'LIVE SERV', 'name': 'Live Serv'},
    {'key': 'SOURCE_CHOICES', 'code': 'GOOGLE', 'name': 'Google'},
    {'key': 'SOURCE_CHOICES', 'code': 'META', 'name': 'Meta'},
    {'key': 'SOURCE_CHOICES', 'code': 'YOUTUBE', 'name': 'Youtube'},
    {'key': 'SOURCE_CHOICES', 'code': 'INSTAGRAM', 'name': 'Instagram'},
    {'key': 'SOURCE_CHOICES', 'code': 'HOARDING', 'name': 'Hoarding'},
    {'key': 'SOURCE_CHOICES', 'code': 'BROKER', 'name': 'Broker'},
    {'key': 'SOURCE_CHOICES', 'code': 'DIRECT', 'name': 'Direct'},

    # LOCATION_CHOICES
    {'key': 'LOCATION_CHOICES', 'code': 'MUMBAI', 'name': 'Mumbai'},
    {'key': 'LOCATION_CHOICES', 'code': 'PUNE', 'name': 'Pune'},
    {'key': 'LOCATION_CHOICES', 'code': 'DELHI', 'name': 'Delhi'},
    {'key': 'LOCATION_CHOICES', 'code': 'BANGALORE', 'name': 'Bangalore'},
    {'key': 'LOCATION_CHOICES', 'code': 'HYDERABAD', 'name': 'Hyderabad'},
    {'key': 'LOCATION_CHOICES', 'code': 'CHENNAI', 'name': 'Chennai'},
    {'key': 'LOCATION_CHOICES', 'code': 'KOLKATA', 'name': 'Kolkata'},
    {'key': 'LOCATION_CHOICES', 'code': 'AHMEDABAD', 'name': 'Ahmedabad'},
    {'key': 'LOCATION_CHOICES', 'code': 'QATAR', 'name': 'Qatar'},
    {'key': 'LOCATION_CHOICES', 'code': 'DUBAI', 'name': 'Dubai'},
]

for c in codes:
    ApplicationCode.objects.update_or_create(
        key=c['key'],
        code=c['code'],
        defaults={
            'name': c['name'],
            'is_active': True,
            'is_delete': False,
            'created_at': now,
            'updated_at': now
        }
    )

print(f'Successfully created/updated {len(codes)} application codes')
