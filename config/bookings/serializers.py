from rest_framework.serializers import ModelSerializer

from .models import Booking


class BookingSerializer(ModelSerializer):

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'accommodation',
            'arrival_date',
            'departure_date',
        ]
