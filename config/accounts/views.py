from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser, OTP
from .serializers import (
    UserRegisterSerializer,
    ResendOTPSerializer,
    PasswordResetConfirmSerializer,
    EmailConfirmationSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
)
from .utils import create_and_send_otp


class UserRegisterAPIView(APIView):
    """
    API для создания новых пользователей.

    Этот эндпоинт позволяет пользователям зарегистрироваться и создать новые учетные записи.

    Пользователи должны предоставить следующую информацию в теле запроса:
    - username: Имя пользователя нового пользователя. Обязательно.
    - email: Адрес электронной почты нового пользователя. Обязательно. Должен быть уникальным.
    - password: Пароль для нового пользователя. Обязательно.
    - confirm_password: Подтверждение пароля. Обязательно.

    Если регистрация прошла успешно, эндпоинт возвращает ответ со статусом 201 (Создано) и следующими данными:
    - message: Сообщение об успехе, указывающее, что пользователь успешно создан.
    - data:
        - username: Имя пользователя созданного пользователя.
        - email: Адрес электронной почты созданного пользователя.

    Если тело запроса недействительно или неполное, эндпоинт возвращает ответ со статусом 400 (Неверный запрос) и сообщением об ошибке, указывающим на ошибки валидации.

    Пример использования:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secretpassword",
        "confirm_password": "secretpassword"
    }
    """

    @swagger_auto_schema(
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response(
                description='Пользователь успешно создан.',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успехе'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email пользователя'),
                            },
                        ),
                    },
                ),
            ),
            400: 'Неверный запрос',
        },
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Пользователь успешно создан.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPAPIView(APIView):
    """
    API для повторной отправки OTP пользователю для верификации почты.


    Этот эндпоинт позволяет повторно отправить OTP пользователю,
    если он не успел ввести OTP для верификации при регистрации.
    """

    @swagger_auto_schema(
        request_body=ResendOTPSerializer,
        responses={
            200: openapi.Response(
                description='OK - OTP успешно отправлен пользователю для верификации',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успешной отправке OTP')
                    }
                )
            ),
            400: openapi.Response(description='Bad Request - неверный формат запроса'),
            404: openapi.Response(description='Not Found - пользователь с указанным адресом электронной почты не найден')
        },
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({
                    'message': 'Пользователь с указанным адресом электронной почты не найден.'
                },
                    status=status.HTTP_404_NOT_FOUND)

            create_and_send_otp(user, "EmailConfirmation")
            return Response({
                'message': 'OTP на указанный адрес успешно отправлен пользователю для верификации.'
            },
                status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailConfirmationAPIView(APIView):
    """
    API для подтверждения email по коду OTP.

    Этот эндпоинт позволяет пользователям подтвердить свой email
    путем ввода кода подтверждения (OTP), отправленного на указанный email.

    При успешном подтверждении email, пользователь аутентифицируется,
    и для него генерируются токены доступа и обновления (JWT).
    """

    @swagger_auto_schema(
        request_body=EmailConfirmationSerializer,
        responses={
            200: openapi.Response(
                description='OK - Email успешно подтвержден',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Email успешно подтвержден'),
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Токен обновления (JWT)'),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='Токен доступа (JWT)'),
                    }
                )
            ),
            400: openapi.Response(description='Bad Request - неверный формат запроса'),
            404: openapi.Response(description='Not Found - пользователь с указанным адресом электронной почты не найден')
        },
    )
    def post(self, request):
        serializer = EmailConfirmationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            otp_value = serializer.validated_data.get('otp')

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response(
                    {'error': 'Пользователь с указанным адресом электронной почты не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                otp = OTP.objects.get(user=user, title="EmailConfirmation", value=otp_value)
                if otp.expired_date < timezone.now() and otp_value.isdigit():
                    return Response(
                        {'error': 'Указанный OTP истек или недействителен'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except OTP.DoesNotExist:
                return Response(
                    {'error': 'Указанный OTP недействителен или не соответствует указанному email'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.email_confirmed = True
            user.save()
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Email успешно подтвержден',
                'username': user.username,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
                status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Аутентификация пользователя.

    Этот эндпоинт предназначен для аутентификации пользователя и получения токенов доступа и обновления (JWT).

    Для аутентификации требуется предоставить правильные учетные данные пользователя:
        - email: адрес электронной почты пользователя
        - password: пароль пользователя

    При успешной аутентификации эндпоинт возвращает токены доступа и обновления, а также имя пользователя.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        request_body=CustomTokenObtainPairSerializer,
        responses={
            200: openapi.Response(
                description="OK - успешная аутентификация",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING, description="Токен доступа (JWT)"),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Токен обновления (JWT)"),
                        "username": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized - Не найдена активная учетная запись с указанными учетными данными"
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomLogoutView(APIView):
    """
    Разлогинивание пользователя.

    Этот эндпоинт позволяет пользователям разлогиниться, что приводит к добавлению токена обновления в черный список
    и прекращению действия токена доступа.

    Для разлогинивания необходимо предоставить токен обновления (JWT) пользователя в теле запроса.

    При успешном разлогинивании эндпоинт возвращает сообщение об успешном разлогинивании.
    """
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Токен обновления (JWT)')
            }
        ),
        responses={
            200: openapi.Response(
                description="OK - Сообщение об успешном разлогинивании",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Пользователь успешно разлогинен.")
                    }
                )
            ),
            400: openapi.Response(description="Bad Request - Необходимо предоставить refresh_token."),
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Пользователь успешно разлогинен."})
        else:
            return Response({
                "error": "Необходимо предоставить refresh_token."
            },
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestAPIView(APIView):
    """
    API для запроса сброса пароля.

    Этот эндпоинт позволяет пользователям запросить сброс пароля
    путем отправки OTP на их зарегистрированный адрес электронной почты.
    """
    def post(self, request):
        """
        POST-запрос для запроса сброса пароля.

        Пользователи должны предоставить следующую информацию в теле запроса:
        - email: Адрес электронной почты пользователя. Обязательно.

        Если запрос успешен и OTP отправлен,
        эндпоинт возвращает ответ со статусом 200 (OK) и сообщением об успешной отправке.

        Если пользователь с указанным адресом электронной почты не найден,
        эндпоинт возвращает ответ со статусом 404 (Not Found) и сообщением об ошибке.
        """
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Необходимо указать адрес электронной почты'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Пользователь с указанным адресом электронной почты не найден'}, status=status.HTTP_404_NOT_FOUND)

        create_and_send_otp(user, otp_title="PasswordReset")

        return Response({'message': 'OTP для сброса пароля успешно отправлен'}, status=status.HTTP_200_OK)


class PasswordResetConfirmAPIView(APIView):
    """
    API для сброса пароля.

    Этот эндпоинт позволяет пользователям сбросить свой пароль
    путем подтверждения кода подтверждения (OTP) и указания нового пароля.
    """
    def post(self, request):
        """
        POST-запрос для сброса пароля.

        Пользователи должны предоставить следующую информацию в теле запроса:
        - email: Адрес электронной почты пользователя. Обязательно.
        - otp: Код подтверждения для сброса пароля. Обязательно.
        - password: Новый пароль пользователя. Обязательно.
        - confirm_password: Подтверждение нового пароля пользователя. Обязательно.

        Если запрос успешен и пароль сброшен,
        эндпоинт возвращает ответ со статусом 200 (OK) и сообщением об успешном сбросе пароля.

        Если указанный OTP недействителен или не соответствует указанному пользователю,
        эндпоинт возвращает ответ со статусом 400 (Bad Request) и сообщением об ошибке.
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            otp_value = serializer.validated_data.get('otp')
            new_password = serializer.validated_data.get('password')

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            try:
                otp = OTP.objects.get(user=user, title="PasswordReset", value=otp_value)
                if otp.expired_date < timezone.now():
                    return Response({'error': 'OTP has expired or is invalid.'}, status=status.HTTP_400_BAD_REQUEST)
            except OTP.DoesNotExist:
                return Response({'error': 'Invalid OTP or does not match the user.'},
                                status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()

            return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountDeletionAPIView(APIView):
    """
    API для удаления аккаунта пользователя.

    Этот эндпоинт позволяет пользователям удалить свой аккаунт без подтверждения действия паролем.
    """

    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        responses={
            204: openapi.Response(description="No Content - Аккаунт успешно удален."),
            401: openapi.Response(description="Unauthorized - Пользователь не авторизован"),
        },
    )
    def delete(self, request):
        request.user.delete()
        return Response({'message': 'Аккаунт успешно удален.'}, status=status.HTTP_204_NO_CONTENT)


class UserProfileAPIView(APIView):
    """
    API для просмотра и обновления профиля пользователя.

    Пользователи могут просматривать и обновлять свой профиль через этот эндпоинт.
    """
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description='Успешный ответ - данные профиля пользователя',
                schema=UserProfileSerializer
            ),
            401: openapi.Response(description='Ошибка авторизации - пользователь не аутентифицирован')
        }
    )
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(description='Успешное обновление - обновленные данные профиля пользователя'),
            400: openapi.Response(description='Ошибка в запросе - неверный формат данных для обновления')
        }
    )
    def put(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
