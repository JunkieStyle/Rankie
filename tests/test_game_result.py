import pytest

from model_bakery import baker
from rest_framework import status
from rest_framework.reverse import reverse

from apps.rankie.models import GameResult


@pytest.fixture
def user(db):
    return baker.make("authx.User", username="John_Doe", is_superuser=False)


@pytest.fixture
def game(db):
    return baker.make("rankie.Game")


@pytest.fixture
def game_results(db, user, game):
    return baker.make("rankie.GameResult", _quantity=10, user=user, game=game)


def test_post_game_result(api_client, user, game):
    url = reverse("api:gameresults-list")
    data = {
        "game": game.label,
        "player": user.username,
        "origin": GameResult.ORIGIN.CUSTOM,
        "text": """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore
                etdolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
                aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
                dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
                officia deserunt mollit anim id est laborum.""",
    }
    api_client.login(username=user.username, password=user.password)
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
