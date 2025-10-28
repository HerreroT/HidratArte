"""
URL configuration for HIDRATARTE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import FileResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
import os

def serve_media(request, path):
    """Servir archivos media con headers CORS correctos."""
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Access-Control-Allow-Origin'] = '*'
        response['Cross-Origin-Resource-Policy'] = 'cross-origin'
        return response
    from django.http import HttpResponseNotFound
    return HttpResponseNotFound('Archivo no encontrado')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Rutas de apps
    path('useradmin/', include('useradmin.urls')),
    path('', include('main.urls')),  # <- así incluís lo de main

    # Rutas JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# Servir archivos media con headers CORS
if settings.MEDIA_URL and settings.MEDIA_ROOT:
    if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    else:
        # En producción: usar vista personalizada con CORS
        urlpatterns += [
            path('media/<path:path>', serve_media, name='serve_media'),
        ]



