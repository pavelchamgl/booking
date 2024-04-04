from rest_framework import generics
from rest_framework import filters
from django_filters import rest_framework as django_filters
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
        'location__city': ['exact'],
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
