from rest_framework import serializers
from .models import Accommodation, AccommodationImage


class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = [
            'id',
            'accommodation',
            'image'
        ]


class AccommodationSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Accommodation
        fields = [
            'id',
            'image',
            'name',
            'rating',
            'adults_capacity',
            'bed_type',
            'wifi_available',
            'cost',
            'currency',
            'available',
        ]

    def get_image(self, accommodation):
        images = accommodation.images.order_by('id')
        return AccommodationImageSerializer(images.first()).data


class AccommodationDetailSerializer(serializers.ModelSerializer):
    images = AccommodationImageSerializer(many=True, read_only=True)

    class Meta:
        model = Accommodation
        fields = [
            'id',
            'images',
            'name',
            'description',
            'rating',
            'adults_capacity',
            'bed_type',
            'wifi_available',
            'cost',
            'currency',
            'available',
        ]
