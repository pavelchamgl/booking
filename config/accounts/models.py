from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150)
    full_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(blank=True, null=True, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name']

    def __str__(self):
        return f"ID: {self.pk}. E-mail: {self.email}"
