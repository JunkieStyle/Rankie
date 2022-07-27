import django_filters

from django.contrib.auth import get_user_model

from apps.rankie.models import League


class LeagueFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    owner = django_filters.ModelChoiceFilter(queryset=get_user_model().objects.all())

    class Meta:
        model = League
        fields = ("name", "owner")
