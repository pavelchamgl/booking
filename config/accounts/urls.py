from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegisterAPIView,
    ResendOTPAPIView,
    PasswordResetConfirmAPIView,
    EmailConfirmationAPIView,
    CustomTokenObtainPairView,
    CustomLogoutView,
    UserProfileAPIView,
    AccountDeletionAPIView,
)

urlpatterns = [
    path('register/', UserRegisterAPIView.as_view(), name='user-registration'),
    path('confirm-email/', EmailConfirmationAPIView.as_view(), name='email_confirmation'),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend_otp'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('reset-password/', PasswordResetConfirmAPIView.as_view(), name='reset_password'),
    path('profile-me/', UserProfileAPIView.as_view(), name='my_profile'),
    path('deletion-me/', AccountDeletionAPIView.as_view(), name='deletion_me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
