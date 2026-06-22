from django.urls import path

from app.api.v1.views.auth import LoginView, RefreshView, RegisterView
from app.api.v1.views.cache_test import CachePingView, CacheTestView
from app.api.v1.views.events import EventsView
from app.api.v1.views.health import HealthView
from app.api.v1.views.media import MediaUploadView, MediaUrlView

urlpatterns = [
    path("health", HealthView.as_view()),
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/refresh", RefreshView.as_view()),
    path("media/upload", MediaUploadView.as_view()),
    path("media/<uuid:media_id>/url", MediaUrlView.as_view()),
    path("events", EventsView.as_view()),
    path("cache/ping", CachePingView.as_view()),
    path("cache/test", CacheTestView.as_view()),
]
