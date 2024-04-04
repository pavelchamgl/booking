from django.urls import path

from .views import AccommodationSearchAPIView


urlpatterns = [
    path('accommodations/search/', AccommodationSearchAPIView.as_view(), name='accommodation-search'),
]
