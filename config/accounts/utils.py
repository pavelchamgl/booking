from random import randint
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import OTP


def create_and_send_otp(user):
    otp_title = "EmailConfirmation"
    value = randint(1000, 9999)

    try:
        otp = OTP.objects.get(user=user, title=otp_title)
        otp.value = value
    except OTP.DoesNotExist:
        otp = OTP.objects.create(user=user, title=otp_title, value=value,
                                 expired_date=timezone.now() + settings.OTP_LIFETIME)

    otp.save()

    subject = "Email Confirmation"
    message = f"Hi {user.username}! You can confirm your email by using code: {value}"
    send_mail(subject, message, "auth_server@admin.com", [user.email])
