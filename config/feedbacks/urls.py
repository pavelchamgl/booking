from django.urls import path

from .views import AccommodationFeedbacks

urlpatterns = [
    path('accommodation/<int:accommodation_id>/', AccommodationFeedbacks.as_view(), name='accommodation-feedbacks')
]
