from rest_framework import serializers
from .models import Accommodation, AccommodationImage


class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = ('image',)


class AccommodationSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Accommodation
        fields = [
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

    def get_image(self, obj):
        image_instance = obj.images.filter(id=1).first()
        if image_instance:
            return AccommodationImageSerializer(image_instance).data
        return None


class AccommodationDetailSerializer(serializers.ModelSerializer):
    images = AccommodationImageSerializer(many=True, read_only=True)

    class Meta:
        model = Accommodation
        fields = [
            'images',
            'name',
            'rating',
            'adults_capacity',
            'bed_type',
            'wifi_available',
            'cost',
            'currency',
            'available',
        ]
