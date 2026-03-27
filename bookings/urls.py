from django.urls import path
from .views import (
    BookingListView, BookingDetailView, BookingCreateView, 
    BookingUpdateView, add_booking_document, delete_booking_document
)
from .api_views import booking_list_api

urlpatterns = [
    path('', BookingListView.as_view(), name='booking_list'),
    path('api/list/', booking_list_api, name='booking_list_api'),
    path('new/', BookingCreateView.as_view(), name='booking_create'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/update/', BookingUpdateView.as_view(), name='booking_update'),
    path('<int:pk>/document/add/', add_booking_document, name='add_booking_document'),
    path('document/<int:pk>/delete/', delete_booking_document, name='delete_booking_document'),
]
