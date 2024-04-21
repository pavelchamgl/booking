from rest_framework.serializers import ModelSerializer, CharField

from .models import Feedback


class FeedbackSerializer(ModelSerializer):
    username = CharField(source='user.username', read_only=True)
    user_image = CharField(source='user.image', read_only=True)

    class Meta:
        model = Feedback
        fields = [
            'id',
            'user',
            'username',
            'user_image',
            'accommodation',
            'text'
        ]
