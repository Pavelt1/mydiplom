from backend_app import views
from django.contrib import admin
from django.urls import include, path

from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path('', views.Index.as_view()),
    path('api/admin/', admin.site.urls),
    path('api/token/', obtain_auth_token),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

]
