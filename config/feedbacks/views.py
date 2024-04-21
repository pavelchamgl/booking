from rest_framework.generics import ListAPIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Feedback
from .serializers import FeedbackSerializer


class AccommodationFeedbacks(ListAPIView):
    """
    Представление для получения обратной связи для определенного размещения.

    Параметры:
        - accommodation_id (int): Идентификатор размещения.

    Ответы:
        - 200: Список объектов обратной связи.
        ПРИМЕЧАНИЕ: ЕСЛИ ВЫ ПОЛУЧАЕТЕ ПУСТОЙ СПИСОК В ОТВЕТЕ [] ВОЗМОЖНО ВЫ ПЫТАЕТЕСЬ ОБРАТИТЬСЯ К НЕСУЩЕСТВУЮЩЕМУ
        ОТЕЛЮ ЛИБО ОТЕЛЬ НЕ ИМЕЕТ ОТЗЫВОВ
    """

    serializer_class = FeedbackSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'accommodation_id',
                openapi.IN_PATH,
                description="Идентификатор размещения",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={200: FeedbackSerializer(many=True)}
    )
    def get_queryset(self):
        accommodation_id = self.kwargs['accommodation_id']
        return Feedback.objects.filter(accommodation_id=accommodation_id)
