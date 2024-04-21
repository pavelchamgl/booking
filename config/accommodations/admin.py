from django.contrib import admin

from .models import Accommodation, AccommodationImage, AccommodationType, StayDate

admin.site.register(Accommodation)
admin.site.register(AccommodationType)
admin.site.register(AccommodationImage)
admin.site.register(StayDate)
