from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from .models import PaymentMilestone, Payment
from .forms import PaymentMilestoneForm, PaymentForm
from bookings.models import Booking

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff or getattr(user, 'user_role', None) in ('ADMIN', 'MANAGER'):
            return Payment.objects.all()
        return Payment.objects.filter(booking__sales_executive=user)

def add_milestone(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = PaymentMilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.booking = booking
            milestone.created_by = request.user
            milestone.save()
            messages.success(request, "Milestone added successfully.")
        else:
            messages.error(request, "Error adding milestone.")
    return redirect('booking_detail', pk=booking_id)

def record_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES, booking=booking)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.received_by = request.user
            payment.created_by = request.user
            payment.save()
            
            # If a milestone was selected, check if it's fully paid
            if payment.milestone:
                # Calculate total paid for this milestone
                total_paid = Payment.objects.filter(milestone=payment.milestone).aggregate(total=models.Sum('amount'))['total'] or 0
                if total_paid >= payment.milestone.amount:
                    payment.milestone.is_paid = True
                    payment.milestone.save()

            messages.success(request, "Payment recorded successfully.")
        else:
            messages.error(request, "Error recording payment.")
    return redirect('booking_detail', pk=booking_id)
