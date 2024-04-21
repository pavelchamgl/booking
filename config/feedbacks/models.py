from django.db import models

from accounts.models import CustomUser
from accommodations.models import Accommodation


class Feedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    text = models.TextField()

