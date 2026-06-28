from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny


def health(request):
    return JsonResponse({'status': 'ok', 'service': 'game-backend-django'})


urlpatterns = [
    # Health check (used by Docker/Kubernetes)
    path('health', health),

    # Django built-in admin
    path('django-admin/', admin.site.urls),

    # API docs (public — AllowAny to bypass global IsAuthenticated)
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]),                          name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny]),   name='swagger-ui'),

    # REST API — same paths Unity SDK already uses
    path('auth/',        include('apps.auth_service.urls')),
    path('profile/',     include('apps.profile.urls')),
    path('leaderboard/', include('apps.leaderboard.urls')),
    path('resources/',   include('apps.resources.urls')),

    # Dashboard (web UI)
    path('', include('apps.dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)