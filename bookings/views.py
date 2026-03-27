from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Booking, BookingDocument
from .forms import BookingForm, BookingDocumentForm
from payments.forms import PaymentMilestoneForm, PaymentForm
from payments.models import PaymentMilestone, Payment
from leads.models import Lead
from django.db.models import Sum

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.none()

class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.object
        context['doc_form'] = BookingDocumentForm()
        context['milestone_form'] = PaymentMilestoneForm()
        context['payment_form'] = PaymentForm(booking=booking)
        context['documents'] = booking.documents.all()
        context['milestones'] = booking.milestones.all()
        context['payments'] = booking.payments.all()
        # Prepare milestone data for template
        milestone_data = {
            str(ms.id): {
                'amount': round(float(ms.amount)),
                'percentage': float(ms.percentage)
            } for ms in context['milestones']
        }
        context['milestone_data'] = milestone_data
        context['agreement_value'] = float(booking.agreement_value)
        return context

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('booking_list')

    def get_initial(self):
        initial = super().get_initial()
        lead_id = self.request.GET.get('lead')
        if lead_id:
            lead = get_object_or_404(Lead, id=lead_id)
            initial['lead'] = lead
            initial['project'] = lead.interested_project
            initial['unit'] = lead.interested_unit
            initial['status'] = 'CONFIRMED'
            initial['sales_executive'] = lead.assigned_to
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        booking = self.object
        
        # Update unit status to BOOKED
        if booking.unit:
            booking.unit.status = 'SOLD'
            booking.unit.save()
        
        # Update lead status to BOOKED
        if booking.lead:
            booking.lead.status = 'SOLD'
            booking.lead.save()

        # Create milestones from project standards
        if booking.project:
            from payments.models import ProjectMilestone, PaymentMilestone
            standard_milestones = ProjectMilestone.objects.filter(project=booking.project)
            for sm in standard_milestones:
                # Calculate amount based on agreement value
                amount = round((booking.agreement_value * sm.percentage) / 100)
                PaymentMilestone.objects.get_or_create(
                    booking=booking,
                    name=sm.name,
                    defaults={
                        'percentage': sm.percentage,
                        'amount': amount
                    }
                )

        # Handle Initial Payment
        initial_amount = form.cleaned_data.get('initial_payment_amount')
        if initial_amount and initial_amount > 0:
            # Create a default milestone for Booking Amount if none exists
            milestone, created = PaymentMilestone.objects.get_or_create(
                booking=booking,
                name="Booking Amount",
                defaults={
                    'amount': round(initial_amount),
                    'percentage': round((initial_amount / (booking.area * booking.sqft_rate) * 100), 2) if booking.area and booking.sqft_rate else 0,
                    'is_paid': True
                }
            )
            
            Payment.objects.create(
                booking=booking,
                milestone=milestone,
                amount=initial_amount,
                payment_date=timezone.now().date(),
                payment_mode=form.cleaned_data.get('initial_payment_mode', 'ONLINE'),
                reference_number=form.cleaned_data.get('initial_payment_reference', ''),
                received_by=self.request.user,
                created_by=self.request.user
            )
            
        messages.success(self.request, "Booking created successfully!")
        return response

class BookingUpdateView(LoginRequiredMixin, UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('booking_list')

    def form_valid(self, form):
        messages.success(self.request, "Booking updated successfully!")
        return super().form_valid(form)

def add_booking_document(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        form = BookingDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.booking = booking
            doc.created_by = request.user
            doc.save()
            messages.success(request, "Document uploaded successfully!")
    return redirect('booking_detail', pk=pk)

def delete_booking_document(request, pk):
    doc = get_object_or_404(BookingDocument, pk=pk)
    booking_pk = doc.booking.pk
    if request.method == 'POST':
        if doc.file:
            doc.file.delete(save=False)
        doc.delete()
        messages.success(request, "Document deleted successfully!")
    return redirect('booking_detail', pk=booking_pk)
