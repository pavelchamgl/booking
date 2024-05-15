from django.urls import path

from .views import (
    AccommodationSearchAPIView,
    ToggleFavoriteAccommodationAPIView,
    FavoriteAccommodationListAPIView,
    AccommodationDetailAPIView,
    SimilarAccommodationsListAPIView,
)


urlpatterns = [
    path('search/', AccommodationSearchAPIView.as_view(), name='accommodation-search'),
    path('<int:id>/toggle_favorite/', ToggleFavoriteAccommodationAPIView.as_view(),
         name='toggle-favorite-accommodation'),
    path('favorite/', FavoriteAccommodationListAPIView.as_view(), name='favorite-accommodations-list'),
    path('<int:pk>/', AccommodationDetailAPIView.as_view(), name='accommodation-detail'),
    path('similar/<int:accommodation_id>/', SimilarAccommodationsListAPIView.as_view(),
         name='similar-accommodations-list'),
]
