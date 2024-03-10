from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import CustomUser
from .serializers import (
    UserRegisterSerializer,
    ResendOTPSerializer,
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

            create_and_send_otp(user)
            return Response({
                'message': 'OTP на указанный адрес успешно отправлен пользователю для верификации.'
            },
                status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
