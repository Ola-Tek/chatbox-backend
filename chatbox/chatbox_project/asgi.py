import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbox_project.settings")

#initialize the asgi application to ensure apps are loaded before module
django_asgi_app = get_asgi_application()

#import websocket routing directly to avid premature model loading
from chat_app.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
        'http' : django_asgi_app,
        'websocket' : AllowedHostsOriginValidator(
            AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        ),
        )
    })

