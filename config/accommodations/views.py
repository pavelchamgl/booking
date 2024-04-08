from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework import filters
from django_filters import rest_framework as django_filters
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Accommodation
from .serializers import AccommodationSerializer


class AccommodationSearchAPIView(generics.ListAPIView):
    """
    Этот эндпоинт предоставляет возможность выполнить поиск размещений с учетом различных параметров фильтрации.

    Пользователи могут использовать этот эндпоинт для поиска размещений, удовлетворяющих определенным критериям, таким как стоимость, тип размещения, наличие завтрака и т.д.

    Данный эндпоинт поддерживает параметры фильтрации в запросе, что позволяет точно настроить результаты поиска в соответствии с потребностями пользователя.

    Параметры запроса:
    - `check_in_date`: Дата заезда гостей. Формат - YYYY-MM-DD.
    - `num_adults`: Количество взрослых гостей.
    - `num_children`: Количество детей гостей.
    - Дополнительные параметры фильтрации, такие как стоимость, тип размещения, наличие завтрака и т.д.

    Ответы:
    - 200 OK: В случае успешного выполнения запроса, возвращается список объектов размещений, удовлетворяющих критериям фильтрации.
        Пример ответа:
        [
            {
                "image": {"image": "url_to_image.jpg"},
                "name": "Название размещения",
                "rating": 9.5,
                "adults_capacity": 2,
                "bed_type": "Двуспальная",
                "wifi_available": true,
                "cost": 100.00,
                "currency": "USD",
                "available": true
            },
            ...
        ]
    - 400 Bad Request: В случае некорректного формата запроса или переданных параметров фильтрации.
    - 404 Not Found: В случае, если размещения, удовлетворяющие заданным критериям, не найдены.
    """

    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer
    filter_backends = [filters.OrderingFilter, django_filters.DjangoFilterBackend]
    ordering_fields = ['cost']
    filterset_fields = {
        'cost': ['lte', 'gte'],
        'accommodation_type__name': ['exact'],
        'breakfast_included': ['exact'],
        'city': ['exact'],
    }

    def get_queryset(self):
        queryset = self.queryset

        check_in_date = self.request.query_params.get('check_in_date')
        num_adults = self.request.query_params.get('num_adults')
        num_children = self.request.query_params.get('num_children')

        if check_in_date:
            queryset = queryset.filter(stay_dates__start_date__lte=check_in_date, stay_dates__end_date__gte=check_in_date)
        if num_adults:
            queryset = queryset.filter(adults_capacity__gte=num_adults)
        if num_children:
            queryset = queryset.filter(children_capacity__gte=num_children)

        return queryset


class ToggleFavoriteAccommodationAPIView(APIView):
    """
    API для добавления/удаления размещения в избранное.

    Этот эндпоинт позволяет пользователям добавлять или удалять размещение в избранное.
    Пользователи могут использовать этот эндпоинт для управления списком своих избранных размещений.

    Для добавления размещения в избранное, пользователь должен отправить PATCH запрос с
    идентификатором размещения в качестве части URL.

    При успешном добавлении размещения в избранное, сервер возвращает сообщение об успешном добавлении
    или удалении размещения в/из избранного со статусом 200 OK.

    Если размещение с указанным идентификатором не найдено, сервер возвращает статус 404 Not Found.

    Ожидаемый запрос:
        PATCH /accommodations/{id}/toggle_favorite/

    Параметры запроса:
    - id (int): Идентификатор размещения.

    Ответы:
        - 200 OK: Успешное добавление или удаление размещения в/из избранного.
            {
                "message": "Accommodation added to favorites."
            }
        - 404 Not Found: Размещение с указанным идентификатором не найдено.
            {
                "error": "Accommodation not found."
            }
    """

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description='OK - Размещение успешно добавлено/удалено из избранного',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение о результате действия'),
                    }
                )
            ),
            400: openapi.Response(description='Bad Request - неверный формат запроса'),
            404: openapi.Response(description='Not Found - размещение не найдено')
        },
    )
    def patch(self, request, id):
        user = request.user

        try:
            accommodation = Accommodation.objects.get(id=id)
        except Accommodation.DoesNotExist:
            return Response({'error': 'Accommodation not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not accommodation.is_favorite.filter(id=user.id).exists():
            accommodation.is_favorite.add(user)
            return Response({'message': 'Accommodation added to favorites.'}, status=status.HTTP_200_OK)
        else:
            accommodation.is_favorite.remove(user)
            return Response({'message': 'Accommodation removed from favorites.'}, status=status.HTTP_200_OK)


class FavoriteAccommodationListAPIView(generics.ListAPIView):
    """
    Этот эндпоинт выводит список избранных отелей пользователя.

    Пользователи могут использовать этот эндпоинт для просмотра списка размещений, которые они добавили в избранное.

    Ожидаемый запрос:
        GET /favorite_accommodations/

    Ожидаемый ответ:
        - 200 OK: Список избранных отелей успешно получен.
    """

    serializer_class = AccommodationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: AccommodationSerializer(many=True)}
    )
    def get_queryset(self):
        user = self.request.user
        return user.favorite_accommodations.all()


class AccommodationDetailAPIView(generics.RetrieveAPIView):
    """
    Этот эндпоинт отображает детальную информацию об отеле.

    Пользователи могут использовать этот эндпоинт для просмотра подробной информации о конкретном размещении.

    Ожидаемый запрос:
        GET /accommodations/<int:pk>/

    Ожидаемый ответ:
        - 200 OK: Возвращает детальную информацию об отеле, включая его изображения и указание на то, добавлен ли отель в избранное пользователем.
        - 404 Not Found: Размещение с указанным идентификатором не найдено.
    """

    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Детальная информация об отеле",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Название отеля'),
                        'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Рейтинг отеля'),
                        'adults_capacity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Вместимость для взрослых'),
                        'bed_type': openapi.Schema(type=openapi.TYPE_STRING, description='Тип кровати'),
                        'wifi_available': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Наличие Wi-Fi'),
                        'cost': openapi.Schema(type=openapi.TYPE_NUMBER, description='Стоимость размещения'),
                        'currency': openapi.Schema(type=openapi.TYPE_STRING, description='Валюта'),
                        'available': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Доступность размещения'),
                        'images': openapi.Schema(type=openapi.TYPE_ARRAY, description='Список изображений отеля', items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Добавлен ли отель в избранное текущим пользователем'),
                    }
                )
            ),
            404: openapi.Response(description='Размещение с указанным идентификатором не найдено')
        }
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        is_favorite = False
        if request.user.is_authenticated:
            is_favorite = instance.is_favorite.filter(id=request.user.id).exists()

        data = serializer.data
        data['is_favorite'] = is_favorite

        return Response(data, status=status.HTTP_200_OK)
