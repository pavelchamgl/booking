from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Neobooking API",
      default_version='v1',
      description="API Neobooking предоставляет доступ к различным запросам, требующим аутентификации "
                  "с помощью токена Bearer. "
                  "Для аутентификации включите 'Bearer {access_token}' в заголовок 'Authorization'.",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('neobooking/admin/', admin.site.urls),
    path('neobooking/accounts/', include("accounts.urls")),
    path('neobooking/accommodations/', include("accommodations.urls")),
    path('neobooking/feedbacks/', include("feedbacks.urls")),
    path('neobooking/bookings/', include("bookings.urls")),

    path('neobooking/swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('neobooking/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('neobooking/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
