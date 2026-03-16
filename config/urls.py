from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from dashboard.api_views import DashboardStatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('courses/', include('courses.urls')),
    path('payments/', include('payments.urls')),
    path('attendance/', include('attendance.urls')),
    path('notifications/', include('notifications.urls')),
    
    # API endpoints
    path('api/', include('config.api_router')),
    path('api/dashboard/', DashboardStatsView.as_view(), name='api-dashboard'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]
