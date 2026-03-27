from django.urls import path
from .views import (
    DashboardView, ApplicationCodeListView, ApplicationCodeCreateView, 
    ApplicationCodeUpdateView, soft_delete_application_code, 
    upload_application_codes, download_code_template
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('codes/', ApplicationCodeListView.as_view(), name='application_code_list'),
    path('codes/create/', ApplicationCodeCreateView.as_view(), name='application_code_create'),
    path('codes/<int:pk>/update/', ApplicationCodeUpdateView.as_view(), name='application_code_update'),
    path('codes/<int:pk>/delete/', soft_delete_application_code, name='application_code_delete'),
    path('codes/upload/', upload_application_codes, name='upload_application_codes'),
    path('codes/template/', download_code_template, name='download_code_template'),
]
