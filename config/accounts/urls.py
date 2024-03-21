from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    UserRegisterAPIView,
    ResendOTPAPIView,
    PasswordResetConfirmAPIView,
    EmailConfirmationAPIView,
)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', UserRegisterAPIView.as_view(), name='user-registration'),
    path('confirm-email/', EmailConfirmationAPIView.as_view(), name='email_confirmation'),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend_otp'),
    path('reset-password/', PasswordResetConfirmAPIView.as_view(), name='reset_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
