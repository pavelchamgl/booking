from django.core.exceptions import ValidationError
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking
from .serializers import BookingSerializer
from accommodations.serializers import AccommodationSerializer

from accommodations.models import Accommodation


class BookingCreateAPIView(CreateAPIView):
    """
    API для создания нового бронирования.

    Параметры запроса:
    - accommodation (integer): ID размещения для бронирования.
    - arrival_date (string): Дата заезда в формате "YYYY-MM-DD".
    - departure_date (string): Дата выезда в формате "YYYY-MM-DD".

    Ответы:
        - 201 Created: Бронирование успешно создано.
        - 400 Bad Request: Если переданные данные некорректны или неполны.
            - "Жилье недоступно для бронирования": Жилье не доступно для бронирования.
            - "Жилье с указанным ID не существует": Жилье с указанным ID не существует.
            - "Некорректные данные": Переданные данные некорректны.
    """
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            accommodation_id = request.data.get("accommodation")
            accommodation = Accommodation.objects.get(id=accommodation_id)
            if not accommodation.available:
                return Response({'error': 'Жилье недоступно для бронирования'}, status=status.HTTP_400_BAD_REQUEST)

            user = self.request.user
            request.data["user"] = user.id
            serializer = BookingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'Бронирование успешно создано'}, status=status.HTTP_201_CREATED)
        except Accommodation.DoesNotExist:
            return Response({'error': 'Жилье с указанным ID не существует'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': 'Некорректные данные'}, status=status.HTTP_400_BAD_REQUEST)


class BookingsListAPIView(ListAPIView):
    """
    API для отображения списка бронирований пользователя в зависимости от типа.

    Параметры запроса:
    - booking_type (string): Тип бронирований для отображения.
        Возможные значения: "past_bookings", "new_bookings", "cancelled_bookings".

    Ответы:
        - 200 OK: Возвращает список бронирований соответствующего типа пользователя.
        ПРИМЕЧАНИЕ: Если в ответе получен пустой список "[]", проверьте синтаксис запроса.
    """

    queryset = Accommodation.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = AccommodationSerializer

    def get_queryset(self):
        user = self.request.user
        booking_type = self.kwargs.get('booking_type')
        now = timezone.now()

        if booking_type == 'past_bookings':
            filter_query = Q(departure_date__lte=now)
        elif booking_type == 'new_bookings':
            filter_query = Q(departure_date__gte=now)
        elif booking_type == 'cancelled_bookings':
            filter_query = Q(is_cancelled=True)

        bookings = Booking.objects.filter(filter_query, user=user)
        return Accommodation.objects.filter(booking__in=bookings)


class BookingCancelAPIView(APIView):
    """
    API для отмены существующего бронирования.

    Параметры запроса:
    - booking_id (integer): Идентификатор бронирования, которое необходимо отменить.

    Ответы:
        - 200 OK: Бронирование успешно отменено.
        - 404 Not Found: Если указанное бронирование не найдено.
        - 400 Bad Request: Если возникла ошибка при обработке запроса. Может возникнуть, если бронирование уже отменено или произошла другая ошибка.

    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('booking_id', in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER, description='Идентификатор бронирования'),
        ],
        responses={
            200: openapi.Response(description='Бронирование успешно отменено'),
            404: openapi.Response(description='Бронирование не найдено'),
            400: openapi.Response(description='Ошибка при обработке запроса. Может возникнуть, если бронирование уже отменено или произошла другая ошибка.')
        }
    )
    def patch(self, request, *args, **kwargs):
        try:
            user = self.request.user
            booking_id = kwargs['booking_id']
            booking = Booking.objects.get(id=booking_id, user=user.id)

            if booking.is_cancelled:
                return Response({'error': 'Бронирование уже отменено'}, status=status.HTTP_400_BAD_REQUEST)

            booking.is_cancelled = True
            booking.save()
            return Response({'successful': 'Бронирование успешно отменено'}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({'error': 'Бронирование не найдено'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



