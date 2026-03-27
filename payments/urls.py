from django.urls import path
from .views import PaymentListView, add_milestone, record_payment

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment_list'),
    path('booking/<int:booking_id>/milestone/add/', add_milestone, name='add_milestone'),
    path('booking/<int:booking_id>/payment/record/', record_payment, name='record_payment'),
]
