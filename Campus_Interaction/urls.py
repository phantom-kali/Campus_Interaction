from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include('core.urls')),
    path("profile/", include("profiles.urls")),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path("marketplace/", include("marketplace.urls")),
    path("messaging/", include("messaging.urls")),
    # path("notifications/", include("notifications.urls")),
    path('events/', include('events.urls')),
    path('polls/', include('polls.urls')),
    path('maps/', include('maps.urls')),
    path('', include('feeds.urls')),
]


if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        re_path(
            r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}
        ),
    ]
else:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
