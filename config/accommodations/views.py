from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import filters
from django_filters import rest_framework as django_filters
from rest_framework.generics import get_object_or_404, ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cloudinary.uploader import upload

from .models import Accommodation
from .serializers import AccommodationSerializer, AccommodationImageSerializer, AccommodationDetailSerializer


class AccommodationSearchAPIView(ListAPIView):
    """
    API для поиска размещений.

    Этот эндпоинт предоставляет возможность выполнить поиск размещений с учетом различных параметров фильтрации.

    Пользователи могут использовать этот эндпоинт для поиска размещений, удовлетворяющих определенным критериям, таким как стоимость, тип размещения, наличие завтрака и т.д.

    Данный эндпоинт поддерживает параметры фильтрации в запросе, что позволяет точно настроить результаты поиска в соответствии с потребностями пользователя.

    Параметры запроса:
    - check_in_date (str): Дата заезда гостей в формате YYYY-MM-DD.
    - num_adults (int): Количество взрослых гостей.
    - num_children (int): Количество детей гостей.
    - city (str): Город, в котором ищется размещение.
    - Дополнительные параметры фильтрации, такие как стоимость (cost), тип размещения (accommodation_type__name), наличие завтрака (breakfast_included) и т.д.

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
        city = self.request.query_params.get('city')

        if check_in_date:
            queryset = queryset.filter(stay_dates__start_date__lte=check_in_date, stay_dates__end_date__gte=check_in_date)
        if num_adults:
            queryset = queryset.filter(adults_capacity__gte=num_adults)
        if num_children:
            queryset = queryset.filter(children_capacity__gte=num_children)
        if city:
            queryset = queryset.filter(city=city)

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


class FavoriteAccommodationListAPIView(ListAPIView):
    """
    API для вывода списка избранных отелей пользователя.

    Пользователи могут использовать этот эндпоинт для просмотра списка размещений, которые они добавили в избранное.

    Ответы:
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


class AccommodationDetailAPIView(RetrieveAPIView):
    """
    API для отображения детальной информации об отеле.

    Пользователи могут использовать этот эндпоинт для просмотра подробной информации о конкретном размещении.

    Ответы:
        - 200 OK: Возвращает детальную информацию об отеле, включая его изображения и указание на то, добавлен ли отель в избранное пользователем.
        - 404 Not Found: Размещение с указанным идентификатором не найдено.
    """

    queryset = Accommodation.objects.all()
    serializer_class = AccommodationDetailSerializer

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


class AccommodationImagesAddCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AccommodationImageSerializer

    def create(self, request, *args, **kwargs):
        accommodation_id = self.kwargs['accommodation_id']
        request.data['accommodation'] = accommodation_id
        image = request.FILES.get('image')
        image_allowed_formats = ['image/png', 'image/jpeg']
        if image.content_type not in image_allowed_formats:
            return Response({'message': 'Неверный формат изображения. Допускаются только форматы PNG и JPEG.'},
                            status=status.HTTP_400_BAD_REQUEST)
        image_response = upload(image, folder="accommodation_images/", resource_type='auto')
        request.data['image'] = image_response['secure_url']
        serializer = AccommodationImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Изображение успешно добавлено', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SimilarAccommodationsListAPIView(ListAPIView):
    """
    API для получения списка похожих размещений.

    Параметры:
    - accommodation_id (int): ID размещения, для которого нужно найти похожие (отели в том же самом городе).

    Ответы:
    - 200 OK: Список похожих размещений.
        - image (str): URL изображения размещения.
        - name (str): Название размещения.
        - rating (float): Рейтинг размещения.
        - adults_capacity (int): Вместимость для взрослых.
        - bed_type (str): Тип кровати.
        - wifi_available (bool): Наличие Wi-Fi.
        - cost (float): Стоимость размещения.
        - currency (str): Валюта стоимости.
        - available (bool): Доступность размещения.
    - 404: Если размещение с предоставленным ID не существует.
    """

    serializer_class = AccommodationSerializer

    def get_queryset(self):
        accommodation_id = self.kwargs['accommodation_id']
        accommodation = get_object_or_404(Accommodation, id=accommodation_id)
        city_accommodations = Accommodation.objects.filter(city=accommodation.city)
        return city_accommodations.exclude(id=accommodation_id)

