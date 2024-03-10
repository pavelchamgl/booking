from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import UserRegisterSerializer


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
