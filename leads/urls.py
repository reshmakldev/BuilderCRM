from django.urls import path
from .views import LeadListView, LeadDetailView, LeadCreateView, LeadUpdateView, add_lead_activity, upload_leads, download_lead_template, LeadAssignView, download_failed_leads, mark_fake_lead
from .api_views import lead_list_api

urlpatterns = [
    path('', LeadListView.as_view(), name='lead_list'),
    path('<int:pk>/', LeadDetailView.as_view(), name='lead_detail'),
    path('create/', LeadCreateView.as_view(), name='lead_create'),
    path('<int:pk>/update/', LeadUpdateView.as_view(), name='lead_update'),
    path('<int:pk>/assign/', LeadAssignView.as_view(), name='lead_assign'),
    path('<int:pk>/add-activity/', add_lead_activity, name='add_lead_activity'),
    path('upload/', upload_leads, name='upload_leads'),
    path('download-template/', download_lead_template, name='download_lead_template'),
    path('download-failed/', download_failed_leads, name='download_failed_leads'),
    path('api/list/', lead_list_api, name='lead_list_api'),
    path('<int:pk>/mark-fake/', mark_fake_lead, name='mark_fake_lead'),
]
