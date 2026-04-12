from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils import timezone

class User(AbstractUser):
    """Custom User model with role selection"""
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Specialization(models.Model):
    """Medical specialization (e.g., Cardiology, Dermatology)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class DoctorProfile(models.Model):
    """Extra information for doctors"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True)
    license_number = models.CharField(max_length=50, unique=True)
    bio = models.TextField(blank=True)
    # Profile picture could be added here

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"

class PatientProfile(models.Model):
    """Extra information for patients"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"

class AvailabilitySlot(models.Model):
    """Doctor's available time slots for appointments"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)  # True if already booked

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'start_time']  # Prevent duplicate slots

    def __str__(self):
        return f"Dr. {self.doctor.user.username} - {self.date} {self.start_time}-{self.end_time}"

class Appointment(models.Model):
    """Appointment booking"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
    )
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    slot = models.ForeignKey(AvailabilitySlot, on_delete=models.CASCADE, related_name='appointments')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    booked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Patient notes for the doctor")

    def __str__(self):
        return f"Appointment: {self.patient.user.username} with Dr.{self.doctor.user.username} on {self.slot.date} at {self.slot.start_time}"