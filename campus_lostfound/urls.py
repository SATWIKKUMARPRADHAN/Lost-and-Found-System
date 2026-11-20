"""
URL configuration for campus_lostfound project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Secondary standard Django Admin interface
    path('django-admin/', admin.site.urls),
    # Core Application Routes
    path('', include('core.urls')),
]

# Serve media files in local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
