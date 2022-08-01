import django_filters as filters

from django.contrib.auth import get_user_model

from apps.rankie.models import Game, League


class LeagueFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    owner = filters.ModelChoiceFilter(queryset=get_user_model().objects.all())
    rule__game = filters.ModelChoiceFilter(queryset=Game.objects.all(), label="Game")
    joined = filters.BooleanFilter(label="Joined", method="get_user_leagues")
    active = filters.BooleanFilter(label="Active", method="get_active")

    class Meta:
        model = League
        fields = ("active", "joined", "public", "name", "rule__game", "owner")

    def get_user_leagues(self, queryset, name, value):
        if value is True:
            return queryset.filter(players__in=[self.request.user])
        elif value is False:
            return queryset.exclude(players__in=[self.request.user])
        return queryset

    # noinspection PyMethodMayBeStatic
    def get_active(self, queryset, name, value):
        if value is True:
            return queryset.active()
        elif value is False:
            return queryset.inactive()
        return queryset
