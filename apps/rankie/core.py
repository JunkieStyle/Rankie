from collections import defaultdict

from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Prefetch, QuerySet
from django.contrib.auth import get_user_model

from .models import Game, Round, League, Standing, GameResult, RoundResult
from .scorers import get_scorer

User = get_user_model()


def get_league_queryset_for_standings_update(player: User, game: Game) -> QuerySet[League]:
    return (
        player.leagues.active()
        .filter(rule__game=game)
        .select_related("rule")
        .prefetch_related(
            Prefetch(
                "rounds",
                Round.objects.order_by("label")
                .select_for_update()
                .prefetch_related(
                    Prefetch(
                        "round_results",
                        RoundResult.objects.order_by("-score", "created"),
                        to_attr="fetched_round_results",
                    )
                ),
                to_attr="fetched_rounds",
            ),
            Prefetch(
                "standings",
                Standing.objects.filter(Q(player=player) | Q(score__isnull=False))
                .order_by("-score", "created")
                .select_for_update(no_key=True),
                to_attr="fetched_standings",
            ),
        )
    )


def register_game_result(game_result: GameResult):
    """Create round/round_result and update corresponding standings for every active league the player competes in."""

    player = game_result.player
    game = game_result.game
    active_leagues = get_league_queryset_for_standings_update(player, game)

    standings_to_update = []
    rounds_to_update = []

    with transaction.atomic():
        # Dict with model classes as keys and lists of instances as values
        objects_to_create = defaultdict(list)

        for league in active_leagues:
            scorer = get_scorer(league)
            round_label = scorer.get_round_label(game_result)

            # Find/create corresponding Round and RoundResult
            curr_round = None
            curr_round_result = None

            curr_round_other_results = []
            other_rounds_results = []

            for fetched_round in league.fetched_rounds:
                if fetched_round.label == round_label:
                    curr_round = fetched_round

                for fetched_result in fetched_round.fetched_round_results:
                    if fetched_result.player == player:
                        if curr_round == fetched_round:
                            curr_round_result = fetched_result
                        else:
                            other_rounds_results.append(fetched_result)
                    elif curr_round == fetched_round:
                        curr_round_other_results.append(fetched_result)

            if curr_round is None:
                curr_round = Round(league=league, label=round_label, mvp=player)
                objects_to_create[Round].append(curr_round)

            if curr_round_result is None:
                curr_round_result = RoundResult(
                    round=curr_round, player=player, score=scorer.get_round_score(game_result), raw=game_result
                )
                objects_to_create[RoundResult].append(curr_round_result)
            else:
                # This league is updated
                continue

            # Mvp condition
            # Current round other results must be sorted in queryset
            mvp_needs_change = (
                player != curr_round.mvp
                and len(curr_round_other_results) > 0
                and curr_round_result.score > curr_round_other_results[0].score
            )

            # Change standings
            # Assume standings are sorted and filtered in queryset (all have scores or from current player)
            curr_rank = 1
            prev_rank = len(league.fetched_standings)
            curr_standing_score = scorer.get_standing_score(other_rounds_results + [curr_round_result])

            for rank, standing in enumerate(league.fetched_standings, 1):
                need_update = False

                if standing.player == player:
                    if standing.rank:
                        prev_rank = rank
                    # Assume other_rounds_results are sorted by round label in queryset
                    standing.score = curr_standing_score
                    standing.rank = curr_rank
                    if mvp_needs_change or curr_round.pk is None:
                        standing.mvp_count += 1
                    need_update = True

                elif curr_standing_score > standing.score and (curr_round <= standing.rank < prev_rank):
                    standing.rank += 1
                    need_update = True
                else:
                    curr_rank += 1

                # Old mvp standing
                if mvp_needs_change and standing.player == curr_round.mvp:
                    standing.mvp_count -= 1
                    need_update = True

                if need_update:
                    standing.updated = timezone.now()
                    standings_to_update.append(standing)

            # Updating mvp
            if mvp_needs_change:
                curr_round.mvp = player
                curr_round.updated = timezone.now()
                rounds_to_update.append(curr_round)

        # Perform bulk db operations
        for model_class, objects in objects_to_create.items():
            model_class.objects.bulk_create(objects)

        Round.objects.bulk_update(rounds_to_update, ["mvp"])
        Standing.objects.bulk_update(standings_to_update, ["updated", "mvp_count", "rank", "score"])
