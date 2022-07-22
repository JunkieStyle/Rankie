from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Game, GameResult


class GameResultModelSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", queryset=get_user_model().objects.all())
    game = serializers.SlugRelatedField(slug_field="name", queryset=Game.objects.all())
    origin = serializers.ChoiceField(choices=GameResult.ORIGIN.choices)

    class Meta:
        model = GameResult
        fields = "__all__"
