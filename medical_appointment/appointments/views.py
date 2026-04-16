from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db.models import Q, Avg
from django.http import JsonResponse
from .models import User, DoctorProfile, PatientProfile, Specialization, AvailabilitySlot, Appointment, DoctorRating
from .forms import UserRegisterForm, AdminUserCreateForm, DoctorProfileForm, PatientProfileForm, AvailabilitySlotForm, AppointmentBookForm
from .decorators import role_required
from django.utils import timezone

# -------- Public Landing Page (no login required) --------
def home(request):
    """Public landing page with doctor search and preview"""
    # Get top 6 doctors for preview
    top_doctors = DoctorProfile.objects.select_related('user', 'specialization').annotate(
        avg_rating=Avg('ratings__rating')
    )[:6]
    
    doctors_data = []
    for doc in top_doctors:
        doctors_data.append({
            'id': doc.id,
            'name': f"Dr. {doc.user.get_full_name() or doc.user.username}",
            'specialization': doc.specialization.name if doc.specialization else 'General',
            'avg_rating': round(doc.avg_rating or 0, 1),
        })
    
    context = {
        'top_doctors': doctors_data,
    }
    return render(request, 'appointments/home.html', context)

# -------- User Dashboard (requires login) --------
@login_required
def dashboard(request):
    """Authenticated user dashboard (was the old home view)"""
    context = {}
    if request.user.role == 'patient':
        patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)
        upcoming = Appointment.objects.filter(
            patient=patient_profile,
            status__in=['pending', 'accepted'],
            slot__date__gte=timezone.now().date()
        )[:5]
        context['upcoming_appointments'] = upcoming
    elif request.user.role == 'doctor':
        doctor_profile, created = DoctorProfile.objects.get_or_create(user=request.user)
        pending = Appointment.objects.filter(
            doctor=doctor_profile,
            status='pending'
        )[:5]
        context['pending_appointments'] = pending
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')
    return render(request, 'appointments/dashboard.html', context)

# -------- Authentication Views --------
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome {user.username}.")
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'appointments/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'appointments/login.html')

def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# ==================== NEW SEARCH & RATING ENDPOINTS ====================
def search_doctors(request):
    """AJAX search endpoint for doctors by name or specialty"""
    query = request.GET.get('q', '')
    specialty = request.GET.get('specialty', '')
    doctors = DoctorProfile.objects.select_related('user', 'specialization').all()
    
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query)
        )
    if specialty:
        doctors = doctors.filter(specialization__name__icontains=specialty)
    
    # Annotate average rating
    doctors = doctors.annotate(avg_rating=Avg('ratings__rating'))
    
    data = []
    for doc in doctors:
        data.append({
            'id': doc.id,
            'name': f"Dr. {doc.user.get_full_name() or doc.user.username}",
            'specialization': doc.specialization.name if doc.specialization else 'General',
            'rating': round(doc.avg_rating or 0, 1),
            'image': '/static/appointments/images/doctor-placeholder.jpg',  # you can change this
        })
    return JsonResponse({'doctors': data})

def rate_doctor(request, doctor_id):
    """Handle rating submission via POST (AJAX)"""
    if not request.user.is_authenticated or request.user.role != 'patient':
        return JsonResponse({'error': 'Only patients can rate'}, status=403)
    
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    patient = request.user.patient_profile
    
    if request.method == 'POST':
        rating_value = int(request.POST.get('rating'))
        comment = request.POST.get('comment', '')
        
        # Update or create rating
        rating, created = DoctorRating.objects.update_or_create(
            doctor=doctor, patient=patient,
            defaults={'rating': rating_value, 'comment': comment}
        )
        
        # Calculate new average
        avg_rating = doctor.ratings.aggregate(Avg('rating'))['rating__avg']
        return JsonResponse({
            'success': True,
            'avg_rating': round(avg_rating or 0, 1),
            'user_rating': rating_value
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)
# ======================================================================

# -------- Patient Views --------
@role_required(['patient'])
def doctor_list(request):
    specializations = Specialization.objects.all()
    selected_spec = request.GET.get('specialization')
    if selected_spec:
        doctors = DoctorProfile.objects.filter(specialization_id=selected_spec)
    else:
        doctors = DoctorProfile.objects.all()
    return render(request, 'appointments/doctor_list.html', {
        'doctors': doctors,
        'specializations': specializations,
        'selected_spec': selected_spec
    })

@role_required(['patient'])
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    if request.method == 'POST':
        form = AppointmentBookForm(request.POST, doctor_id=doctor_id)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient_profile
            appointment.doctor = doctor
            appointment.slot = form.cleaned_data['slot']
            appointment.save()
            slot = appointment.slot
            slot.is_booked = True
            slot.save()
            messages.success(request, f"Appointment booked with Dr. {doctor.user.username} on {slot.date} at {slot.start_time}.")
            return redirect('patient_appointments')
    else:
        form = AppointmentBookForm(doctor_id=doctor_id)
    return render(request, 'appointments/book_appointment.html', {'form': form, 'doctor': doctor})

@role_required(['patient'])
def patient_appointments(request):
    appointments = Appointment.objects.filter(patient=request.user.patient_profile).order_by('-slot__date', '-slot__start_time')
    return render(request, 'appointments/patient_appointments.html', {'appointments': appointments})

@role_required(['patient'])
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient_profile)
    if appointment.status in ['pending', 'accepted']:
        appointment.status = 'canceled'
        appointment.save()
        slot = appointment.slot
        slot.is_booked = False
        slot.save()
        messages.success(request, "Appointment cancelled successfully.")
    else:
        messages.error(request, "Cannot cancel this appointment.")
    return redirect('patient_appointments')

# -------- Doctor Views --------
@role_required(['doctor'])
def doctor_appointments(request):
    appointments = Appointment.objects.filter(doctor=request.user.doctor_profile).order_by('-slot__date', '-slot__start_time')
    return render(request, 'appointments/doctor_appointments.html', {'appointments': appointments})

@role_required(['doctor'])
def update_appointment_status(request, appointment_id, status):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor_profile)
    if status in ['accepted', 'rejected']:
        appointment.status = status
        appointment.save()
        if status == 'rejected':
            slot = appointment.slot
            slot.is_booked = False
            slot.save()
        messages.success(request, f"Appointment {status}.")
    else:
        messages.error(request, "Invalid action.")
    return redirect('doctor_appointments')

@role_required(['doctor'])
def manage_availability(request):
    slots = AvailabilitySlot.objects.filter(doctor=request.user.doctor_profile).order_by('date', 'start_time')
    return render(request, 'appointments/manage_availability.html', {'slots': slots})

@method_decorator(role_required(['doctor']), name='dispatch')
class AvailabilityCreateView(CreateView):
    model = AvailabilitySlot
    form_class = AvailabilitySlotForm
    template_name = 'appointments/availability_form.html'
    success_url = reverse_lazy('manage_availability')

    def form_valid(self, form):
        form.instance.doctor = self.request.user.doctor_profile
        return super().form_valid(form)

@method_decorator(role_required(['doctor']), name='dispatch')
class AvailabilityUpdateView(UpdateView):
    model = AvailabilitySlot
    form_class = AvailabilitySlotForm
    template_name = 'appointments/availability_form.html'
    success_url = reverse_lazy('manage_availability')

    def get_queryset(self):
        return AvailabilitySlot.objects.filter(doctor=self.request.user.doctor_profile)

@method_decorator(role_required(['doctor']), name='dispatch')
class AvailabilityDeleteView(DeleteView):
    model = AvailabilitySlot
    template_name = 'appointments/availability_confirm_delete.html'
    success_url = reverse_lazy('manage_availability')

    def get_queryset(self):
        return AvailabilitySlot.objects.filter(doctor=self.request.user.doctor_profile)

# -------- Admin Views --------
@role_required(['admin'])
def admin_dashboard(request):
    total_users = User.objects.count()
    total_doctors = DoctorProfile.objects.count()
    total_patients = PatientProfile.objects.count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    context = {
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
    }
    return render(request, 'appointments/admin_dashboard.html', context)

# Admin User Management - using AdminUserCreateForm (allows admin role)
@role_required(['admin'])
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'appointments/admin_users.html', {'users': users})

@role_required(['admin'])
def admin_user_create(request):
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect('admin_users')
    else:
        form = AdminUserCreateForm()
    return render(request, 'appointments/admin_user_form.html', {'form': form, 'title': 'Create User'})

@role_required(['admin'])
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect('admin_users')
    else:
        form = AdminUserCreateForm(instance=user)
    return render(request, 'appointments/admin_user_form.html', {'form': form, 'title': 'Edit User'})

@role_required(['admin'])
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot delete superuser.")
    else:
        user.delete()
        messages.success(request, "User deleted.")
    return redirect('admin_users')

# Admin Specialization Management
@role_required(['admin'])
def admin_specializations(request):
    specializations = Specialization.objects.all()
    return render(request, 'appointments/admin_specializations.html', {'specializations': specializations})

@role_required(['admin'])
def admin_specialization_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Specialization.objects.create(name=name, description=description)
        messages.success(request, "Specialization added.")
        return redirect('admin_specializations')
    return render(request, 'appointments/admin_specialization_form.html', {'title': 'Add Specialization'})

@role_required(['admin'])
def admin_specialization_edit(request, spec_id):
    spec = get_object_or_404(Specialization, id=spec_id)
    if request.method == 'POST':
        spec.name = request.POST.get('name')
        spec.description = request.POST.get('description')
        spec.save()
        messages.success(request, "Specialization updated.")
        return redirect('admin_specializations')
    return render(request, 'appointments/admin_specialization_form.html', {'spec': spec, 'title': 'Edit Specialization'})

@role_required(['admin'])
def admin_specialization_delete(request, spec_id):
    spec = get_object_or_404(Specialization, id=spec_id)
    spec.delete()
    messages.success(request, "Specialization deleted.")
    return redirect('admin_specializations')

# Admin Doctor Management
@role_required(['admin'])
def admin_doctors(request):
    doctors = DoctorProfile.objects.select_related('user', 'specialization').all()
    return render(request, 'appointments/admin_doctors.html', {'doctors': doctors})

@role_required(['admin'])
def admin_doctor_edit(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor profile updated.")
            return redirect('admin_doctors')
    else:
        form = DoctorProfileForm(instance=doctor)
    return render(request, 'appointments/admin_doctor_form.html', {'form': form, 'doctor': doctor})

# Admin View All Appointments
@role_required(['admin'])
def admin_appointments(request):
    appointments = Appointment.objects.select_related('patient__user', 'doctor__user', 'slot').all().order_by('-slot__date')
    return render(request, 'appointments/admin_appointments.html', {'appointments': appointments})

# -------- Profile Management --------
@login_required
def profile_view(request):
    if request.user.role == 'doctor':
        profile = request.user.doctor_profile
        form_class = DoctorProfileForm
    elif request.user.role == 'patient':
        profile = request.user.patient_profile
        form_class = PatientProfileForm
    else:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('dashboard')
    else:
        form = form_class(instance=profile)
    return render(request, 'appointments/profile_form.html', {'form': form, 'role': request.user.role})