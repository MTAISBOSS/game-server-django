import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.dashboard.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    'http':      get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(apps.dashboard.routing.websocket_urlpatterns)
    ),
})
