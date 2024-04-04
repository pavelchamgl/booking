from django.db import models


class AccommodationType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Accommodation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    city = models.CharField(max_length=100)
    accommodation_type = models.ForeignKey(AccommodationType, on_delete=models.CASCADE)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    adults_capacity = models.IntegerField()
    children_capacity = models.IntegerField()
    breakfast_included = models.BooleanField(default=False)
    kitchen_available = models.BooleanField(default=False)
    bed_type = models.CharField(max_length=50)
    wifi_available = models.BooleanField(default=True)
    available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1)

    def __str__(self):
        return self.name


class AccommodationImage(models.Model):
    accommodation = models.ForeignKey(Accommodation, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='accommodation_images/')


class StayDate(models.Model):
    accommodation = models.ForeignKey(Accommodation, related_name='stay_dates', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
