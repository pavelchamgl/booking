from django.urls import path

from .views import BookingCreateAPIView, BookingsListAPIView, BookingCancelAPIView

urlpatterns = [
    path('create/', BookingCreateAPIView.as_view(), name='booking_create'),
    path('list/<str:booking_type>/', BookingsListAPIView.as_view(), name='bookings_list'),
    path('cancel/<int:booking_id>/', BookingCancelAPIView.as_view(), name='cancel-booking'),
]
