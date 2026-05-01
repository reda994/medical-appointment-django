from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, DoctorProfile, PatientProfile, Specialization, AvailabilitySlot, Appointment
from django.utils import timezone

class UserRegisterForm(UserCreationForm):
    """Form for public user registration - Patient or Doctor, with specialization for doctors"""
    PUBLIC_ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )
    role = forms.ChoiceField(choices=PUBLIC_ROLE_CHOICES, initial='patient')
    email = forms.EmailField(required=True)
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.all(),
        required=False,
        empty_label="Select your specialization (for doctors)"
    )
    license_number = forms.CharField(
        max_length=50,
        required=False,
        help_text="Required for doctors."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'specialization', 'license_number']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        license_number = cleaned_data.get('license_number')

        if role == 'doctor':
            if not license_number:
                self.add_error('license_number', 'License number is required for doctors.')
            elif DoctorProfile.objects.filter(license_number=license_number).exists():
                self.add_error('license_number', 'This license number is already registered.')
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style the specialization field (hide initially, JS will show for doctor)
        self.fields['specialization'].widget.attrs.update({'class': 'specialization-field'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            # Create profile based on role
            if user.role == 'doctor':
                doctor_profile = DoctorProfile.objects.create(
                    user=user,
                    license_number=self.cleaned_data.get('license_number', '')
                )
                specialization = self.cleaned_data.get('specialization')
                if specialization:
                    doctor_profile.specialization = specialization
                    doctor_profile.save()
            elif user.role == 'patient':
                PatientProfile.objects.create(user=user)
        return user

class AdminUserCreateForm(UserCreationForm):
    """Form for admin to create any user (including admin role)"""
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='patient')
    email = forms.EmailField(required=True)
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.all(),
        required=False,
        empty_label="Select specialization (for doctors)"
    )
    license_number = forms.CharField(
        max_length=50,
        required=False,
        help_text="Required for doctors."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'specialization', 'license_number']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        license_number = cleaned_data.get('license_number')

        if role == 'doctor':
            if not license_number:
                self.add_error('license_number', 'License number is required for doctors.')
            elif DoctorProfile.objects.filter(license_number=license_number).exists():
                self.add_error('license_number', 'This license number is already registered.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            # Create profile only for patient/doctor, not admin
            if user.role == 'doctor':
                doctor_profile = DoctorProfile.objects.create(
                    user=user,
                    license_number=self.cleaned_data.get('license_number', '')
                )
                specialization = self.cleaned_data.get('specialization')
                if specialization:
                    doctor_profile.specialization = specialization
                    doctor_profile.save()
            elif user.role == 'patient':
                PatientProfile.objects.create(user=user)
        return user

class DoctorProfileForm(forms.ModelForm):
    """Form for doctor to update profile"""
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'license_number', 'bio']

class PatientProfileForm(forms.ModelForm):
    """Form for patient to update profile"""
    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'phone', 'address']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class AvailabilitySlotForm(forms.ModelForm):
    """Form for doctors to add/edit availability slots"""
    class Meta:
        model = AvailabilitySlot
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data

class AppointmentBookForm(forms.ModelForm):
    """Form for patient to book an appointment - dynamic doctor and slot selection"""
    class Meta:
        model = Appointment
        fields = ['notes']

    def __init__(self, *args, **kwargs):
        self.doctor_id = kwargs.pop('doctor_id', None)
        super().__init__(*args, **kwargs)
        if self.doctor_id:
            available_slots = AvailabilitySlot.objects.filter(
                doctor_id=self.doctor_id,
                is_booked=False,
                date__gte=timezone.now().date()
            )
            self.fields['slot'] = forms.ModelChoiceField(
                queryset=available_slots,
                empty_label="Select available time slot",
                widget=forms.Select(attrs={'class': 'form-control'})
            )