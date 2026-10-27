from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import ResourseViewSet

router = DefaultRouter()
router.register('user/resource', ResourseViewSet, basename='user-resource')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('api/users/', include('users.urls')),
    path('resources/', include('resourses.urls')),
    path('resourses/', include('resourses.urls')),
    path('api/resources/', include('resourses.urls')),
    path('api/resourses/', include('resourses.urls')),
    path('', include(router.urls)),
]
