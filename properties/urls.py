from django.urls import path
from .views import (
    ProjectListView, ProjectDetailView, ProjectCreateView, 
    UnitCreateView, ProjectUpdateView, UnitUpdateView, 
    UnitUploadView, unit_list_api, add_project_milestone, edit_project_milestone
)

urlpatterns = [
    path('', ProjectListView.as_view(), name='property_list'),
    path('create/', ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/edit/', ProjectUpdateView.as_view(), name='project_edit'),
    path('<int:project_pk>/add-unit/', UnitCreateView.as_view(), name='unit_create'),
    path('<int:project_pk>/upload-units/', UnitUploadView.as_view(), name='unit_upload'),
    path('unit/<int:pk>/edit/', UnitUpdateView.as_view(), name='unit_edit'),
    path('api/units/', unit_list_api, name='unit_list_api'),
    path('<int:pk>/add-milestone/', add_project_milestone, name='add_project_milestone'),
    path('milestone/<int:milestone_pk>/edit/', edit_project_milestone, name='edit_project_milestone'),
]
