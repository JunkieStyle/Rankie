from rest_framework import viewsets

from .models import GameResult
from .serializers import GameResultModelSerializer


class GameResultViewSet(viewsets.ModelViewSet):
    queryset = GameResult.objects.all()
    serializer_class = GameResultModelSerializer
