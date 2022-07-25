from rest_framework import viewsets
from rest_framework.decorators import action

from .core import register_game_result
from .models import GameResult
from .serializers import GameResultModelSerializer


class GameResultViewSet(viewsets.ModelViewSet):
    queryset = GameResult.objects.all()
    serializer_class = GameResultModelSerializer

    @action(methods=["GET"], detail=True)
    def register(self, request, *args, **kwargs):
        game_result = self.get_object()
        register_game_result(game_result)
