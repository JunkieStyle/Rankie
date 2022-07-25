from datetime import timedelta

import pytest

from django.utils import timezone
from model_bakery import baker
from django.contrib.auth import get_user_model

from apps.rankie.models import League, Standing

User = get_user_model()


@pytest.fixture
def leagues(db):
    now = timezone.now()
    return [
        # active
        baker.make(League, start_dt=now - timedelta(days=1), end_dt=now + timedelta(days=1)),
        baker.make(League, start_dt=now - timedelta(days=1), end_dt=None),
        # inactive
        baker.make(League, start_dt=now + timedelta(days=1)),
        baker.make(League, end_dt=now - timedelta(days=1)),
    ]


def test_league_active_manager(db, leagues):
    assert League.objects.inactive().count() == 2
    assert League.objects.active().count() == 2


def test_league_active_manager_related(db, leagues):
    user_1 = baker.make(User)
    user_2 = baker.make(User)
    for league, user in zip(leagues, [user_1, user_2, user_1, user_2]):
        baker.make(Standing, league=league, player=user)
    assert user_1.leagues.inactive().count() == 1
    assert user_1.leagues.active().count() == 1


def test_league_active_method(leagues):
    assert leagues[0].is_active()
    assert leagues[1].is_active()
    assert not leagues[2].is_active()
    assert not leagues[3].is_active()
