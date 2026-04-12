# from django.contrib import admin
# from django.urls import path, include

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('appointments.urls')),
# ]


from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('appointments.urls')),  # Move this BEFORE admin/
    path('admin/', admin.site.urls),
]