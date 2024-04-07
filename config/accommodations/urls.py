from django.urls import path

from .views import (
    AccommodationSearchAPIView,
    ToggleFavoriteAccommodationAPIView,
    FavoriteAccommodationListAPIView,
)


urlpatterns = [
    path('accommodations/search/', AccommodationSearchAPIView.as_view(), name='accommodation-search'),
    path('accommodations/<int:pk>/toggle_favorite/', ToggleFavoriteAccommodationAPIView.as_view(),
         name='toggle-favorite-accommodation'),
    path('favorite_accommodations/', FavoriteAccommodationListAPIView.as_view(), name='favorite-accommodations-list'),
]
