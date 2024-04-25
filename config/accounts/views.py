from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from cloudinary.uploader import upload

from .models import CustomUser, OTP
from .serializers import (
    UserRegisterSerializer,
    EmailSerializer,
    PasswordResetConfirmSerializer,
    EmailConfirmationSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
)
from .utils import create_and_send_otp


class UserRegisterAPIView(APIView):
    """
    API для создания новых пользователей.

    Этот эндпоинт позволяет пользователям регистрироваться и создавать новые учетные записи.

    Параметры запроса:
    - username (строка): Имя пользователя нового пользователя. Обязательно.
    - email (строка): Адрес электронной почты нового пользователя. Обязательно. Должен быть уникальным.
    - password (строка): Пароль для нового пользователя. Обязательно.
    - confirm_password (строка): Подтверждение пароля. Обязательно.

    Ответы:
        - 201 Created: Пользователь успешно создан.
            {
                "message": "Пользователь успешно создан.",
                "data": {
                    "username": "Имя пользователя",
                    "email": "Email пользователя"
                }
            }
        - 400 Bad Request: Неверный запрос, содержит сообщение об ошибках валидации.
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


class SendOTPForEmailVerificationAPIView(APIView):
    """
    API для повторной отправки OTP для верификации по электронной почте.

    Отправляет OTP (одноразовый пароль) на адрес электронной почты пользователя для верификации.

    Параметры:
        - email (строка): Адрес электронной почты пользователя для отправки OTP. Обязательно.

    Ответы:
        - 200 OK: OTP успешно отправлен пользователю для верификации.
        - 400 Bad Request: Неверный формат запроса.
        - 404 Not Found: Пользователь с указанным адресом электронной почты не найден.
    """

    @swagger_auto_schema(
        request_body=EmailSerializer,
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
        serializer = EmailSerializer(data=request.data)
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

    Параметры запроса:
        - email (строка): Адрес электронной почты пользователя для подтверждения. Обязательно.
        - otp (строка): Код подтверждения (OTP). Обязательно.

    Ответы:
        - 200 OK: Email успешно подтвержден. Возвращает данные пользователя и JWT токены доступа и обновления.
            {
                "message": "Email успешно подтвержден",
                "username": "Имя пользователя",
                "refresh": "Токен обновления (JWT)",
                "access": "Токен доступа (JWT)"
            }
        - 400 Bad Request: Неверный формат запроса или указанный OTP недействителен или истек.
        - 404 Not Found: Пользователь с указанным адресом электронной почты не найден.
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
    API для аутентификации пользователей и выдачи токенов доступа и обновления (JWT).

    Параметры запроса:
        - email (строка): Адрес электронной почты пользователя. Обязательно.
        - password (строка): Пароль пользователя. Обязательно.

    Ответы:
        - 200 OK: Успешная аутентификация. Возвращает токены доступа и обновления, а также имя пользователя.
            {
                "access": "Токен доступа (JWT)",
                "refresh": "Токен обновления (JWT)",
                "username": "Имя пользователя"
            }
        - 401 Unauthorized: Не найдена активная учетная запись с указанными учетными данными.
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
    API для разлогинивания пользователя.

    Этот эндпоинт позволяет пользователям разлогиниться, что приводит к добавлению токена обновления в черный список
    и прекращению действия токена доступа.

    Параметры запроса:
        - refresh (строка): Токен обновления (JWT). Обязательно.

    Ответы:
        - 200 OK: Сообщение об успешном разлогинивании.
            {
                "message": "Пользователь успешно разлогинен."
            }
        - 400 Bad Request: Необходимо предоставить refresh_token.
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


class SendOTPForPasswordResetAPIView(APIView):
    """
    API для отправки OTP (одноразового пароля) на адрес электронной почты пользователя для сброса пароля.

    Параметры запроса:
        - email (строка): Адрес электронной почты пользователя. Обязательно.

    Ответы:
        - 200 OK: OTP для сброса пароля успешно отправлен.
        - 400 Bad Request: Неверный формат запроса.
        - 404 Not Found: Пользователь с указанным адресом электронной почты не найден.
    """

    @swagger_auto_schema(
        request_body=EmailSerializer,
        responses={
            200: openapi.Response(
                description='OK - OTP для сброса пароля успешно отправлен',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение об успешной отправке OTP для сброса пароля')
                    }
                )
            ),
            400: openapi.Response(description='Bad Request - неверный формат запроса'),
            404: openapi.Response(description='Not Found - пользователь с указанным адресом электронной почты не найден')
        },
    )
    def post(self, request):
        serializer = EmailSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({
                    'message': 'Пользователь с указанным адресом электронной почты не найден.'
                },
                    status=status.HTTP_404_NOT_FOUND)

            create_and_send_otp(user, otp_title="PasswordReset")
            return Response({'message': 'OTP для сброса пароля успешно отправлен'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmationAPIView(APIView):
    """
    API для подтверждения сброса пароля.

    Этот эндпоинт предназначен для подтверждения сброса пароля пользователя
    путем ввода кода подтверждения (OTP), отправленного на адрес электронной почты,
    и указания нового пароля.

    Параметры запроса:
        - email (строка): Адрес электронной почты пользователя. Обязательно.
        - otp (строка): Код подтверждения (OTP). Обязательно.
        - password (строка): Новый пароль. Обязательно.

    Ответы:
        - 200 OK: Пароль успешно сброшен.
            {
                "message": "Пароль успешно сброшен."
            }
        - 400 Bad Request: Неверный формат запроса или указанный OTP истек или недействителен.
        - 404 Not Found: Пользователь с указанным адресом электронной почты не найден.
            {
                "error": "Пользователь с указанным адресом электронной почты не найден."
            }
    """

    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(
                description="OK - Пароль успешно сброшен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Пароль успешно сброшен.")
                    }
                )
            ),
            400: openapi.Response(description="Bad Request - Неверный формат запроса или указанный OTP истек или недействителен."),
            404: openapi.Response(description="Not Found - Пользователь с указанным адресом электронной почты не найден.")
        }
    )
    def post(self, request):
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
    API для удаления аккаунта пользователя, без подтверждения действия паролем

    Ответы:
        - 204 No Content: Аккаунт успешно удален.
        - 401 Unauthorized: Пользователь не авторизован.
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


class UserProfileGetAPIView(APIView):
    """
    API для просмотра профиля пользователя.

    Пользователи могут просматривать свой профиль через этот эндпоинт.

    Поля профиля:
    - username: Строка до 150 символов.
    - full_name: Строка до 150 символов, может быть пустым.
    - email: Строка, представляющая действительный email адрес. Уникальное значение.
    - image: Изображение формата PNG/JPEG.
    - phone_number: Строка в международном формате, может быть пустым. Уникальное значение.
    - birthday: Дата в формате "YYYY-MM-DD", может быть пустым.
    - email_confirmed: Булево значение. True, если email подтвержден, иначе False.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: UserProfileSerializer(),
            401: "Unauthorized - Пользователь не аутентифицирован"
        }
    )
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class UserProfileUpdateAPIView(APIView):
    """
    API для обновления профиля пользователя.

    Пользователи обновлять свой профиль через этот эндпоинт.

    Поля профиля:
    - username: Строка до 150 символов.
    - full_name: Строка до 150 символов, может быть пустым.
    - email: Строка, представляющая действительный email адрес. Уникальное значение.
    - image: Изображение формата PNG/JPEG.
    - phone_number: Строка в международном формате, может быть пустым. Уникальное значение.
    - birthday: Дата в формате "YYYY-MM-DD", может быть пустым.
    - email_confirmed: Булево значение. True, если email подтвержден, иначе False.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer(),
            400: "Ошибка в запросе - неверный формат данных для обновления",
            401: "Unauthorized - Пользователь не аутентифицирован"
        }
    )
    def patch(self, request):
        user = request.user
        image = request.FILES.get('image')
        if image:
            image_allowed_formats = ['image/png', 'image/jpeg']
            if image.content_type not in image_allowed_formats:
                return Response({'message': 'Неверный формат изображения. Допускаются только форматы PNG и JPEG.'},
                                status=status.HTTP_400_BAD_REQUEST)
            image_response = upload(image, folder="profiles_images/", resource_type='auto')
            request.data['image'] = image_response['secure_url']
        if 'email' not in request.data:
            request.data['email'] = user.email
        if 'username' not in request.data:
            request.data['username'] = user.username
        serializer = UserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(TokenRefreshView):
    """
    API для обновления токена доступа (JWT).

    Этот эндпоинт позволяет автоматически обновлять токен доступа.

    Ожидаемые ответы:
        - 200 OK: Токен доступа успешно обновлен.
            {
                "access": "новый токен доступа (JWT)"
            }
        - 400 Bad Request: Если возникла ошибка при обновлении токена доступа.
            {
                "error": "Ошибка при обновлении токена доступа."
            }
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="OK - Токен доступа успешно обновлен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING, description="Новый токен доступа (JWT)")
                    }
                )
            ),
            400: openapi.Response(description="Bad Request - Ошибка при обновлении токена доступа",
                                   schema=openapi.Schema(
                                       type=openapi.TYPE_OBJECT,
                                       properties={
                                           "error": openapi.Schema(type=openapi.TYPE_STRING,
                                                                   description="Ошибка при обновлении токена доступа.")
                                       }
                                   )),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

