from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('tracker.urls')),
    path('', include('nasa.urls')),
    path('', include('launches.urls')),
    path('', include('airplanes.urls')),
]
