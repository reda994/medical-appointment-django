from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Patient
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('my-appointments/', views.patient_appointments, name='patient_appointments'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    
    # Doctor
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/update-status/<int:appointment_id>/<str:status>/', views.update_appointment_status, name='update_appointment_status'),
    path('doctor/availability/', views.manage_availability, name='manage_availability'),
    path('doctor/availability/add/', views.AvailabilityCreateView.as_view(), name='availability_add'),
    path('doctor/availability/edit/<int:pk>/', views.AvailabilityUpdateView.as_view(), name='availability_edit'),
    path('doctor/availability/delete/<int:pk>/', views.AvailabilityDeleteView.as_view(), name='availability_delete'),
    
    # Search & Rating
    path('search-doctors/', views.search_doctors, name='search_doctors'),
    path('rate-doctor/<int:doctor_id>/', views.rate_doctor, name='rate_doctor'),
    
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin/users/edit/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),
    path('admin/users/delete/<int:user_id>/', views.admin_user_delete, name='admin_user_delete'),
    path('admin/specializations/', views.admin_specializations, name='admin_specializations'),
    path('admin/specializations/create/', views.admin_specialization_create, name='admin_specialization_create'),
    path('admin/specializations/edit/<int:spec_id>/', views.admin_specialization_edit, name='admin_specialization_edit'),
    path('admin/specializations/delete/<int:spec_id>/', views.admin_specialization_delete, name='admin_specialization_delete'),
    path('admin/doctors/', views.admin_doctors, name='admin_doctors'),
    path('admin/doctors/edit/<int:doctor_id>/', views.admin_doctor_edit, name='admin_doctor_edit'),
    path('admin/appointments/', views.admin_appointments, name='admin_appointments'),
]