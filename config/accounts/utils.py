from random import randint
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import OTP


def create_and_send_otp(user):
    otp_value = randint(1000, 9999)
    otp_title = "EmailConfirmation"
    OTP.objects.create(user=user, title=otp_title, value=otp_value, expired_date=timezone.now() + settings.OTP_LIFETIME)

    subject = "Email Confirmation"
    message = f"Hi {user.username}! You can confirm your email by using code: {otp_value}"
    send_mail(subject, message, "auth_server@admin.com", [user.email])
