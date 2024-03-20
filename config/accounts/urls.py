from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    UserRegisterAPIView,
    ResendOTPAPIView,
    PasswordResetConfirmAPIView,
)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', UserRegisterAPIView.as_view(), name='user-registration'),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend_otp'),
    path('reset-password/', PasswordResetConfirmAPIView, name='reset_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
