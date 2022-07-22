from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import GameResult


class GameResultModelSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", queryset=get_user_model().objects.all())

    class Meta:
        model = GameResult
        fields = "__all__"
