from pathlib import Path

import pandas as pd
import pytest

from surebets.matching import find_opportunities, game_key, nickname, player_key

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def book(rows):
    cols = ["website", "game", "market", "team", "player", "line", "more", "less"]
    return pd.DataFrame(rows, columns=cols)


def test_game_key_ignores_home_away_order():
    assert game_key("boston-celtics-vs-miami-heat") == game_key("miami-heat-vs-boston-celtics")


@pytest.mark.parametrize("raw", ["LAL Lakers", "Los Angeles Lakers", "LA Lakers"])
def test_team_aliases_share_a_nickname(raw):
    assert nickname(raw) == "Lakers"


def test_two_word_nickname():
    assert nickname("POR Trail Blazers") == "Trail Blazers"


def test_player_names_are_accent_insensitive():
    assert player_key("Nikola Jokić") == player_key("nikola jokic")


def test_player_prop_matches_across_languages_and_spellings():
    a = book([["pinnacle", None, "Assists", None, "Luka Doncic", 8.5, 1.90, 1.90]])
    b = book([["teapuesto", None, "Asistencias Más/Menos", None, "Luka Dončić", 8.5, 1.85, 2.15]])
    [opp] = find_opportunities(a, b)
    assert [leg.selection for leg in opp.legs] == ["over", "under"]
    assert opp.roi == pytest.approx(1 / (1 / 1.90 + 1 / 2.15) - 1)


def test_different_lines_are_not_compared():
    a = book([["pinnacle", "a-heat-vs-b-celtics", "total", None, None, 218.5, 2.30, 1.60]])
    b = book([["teapuesto", "b-celtics-vs-a-heat", "total", None, None, 219.5, 1.60, 2.30]])
    assert find_opportunities(a, b) == []


def test_handicap_pairs_opposite_teams_at_opposite_lines():
    a = book([["pinnacle", "boston-celtics-vs-miami-heat", "handicap", "Boston Celtics", None, -4.5, 1.93, None]])
    b = book([
        ["teapuesto", "miami-heat-vs-boston-celtics", "handicap", "MIA Heat", None, 4.5, 2.10, None],
        # same team on both books is not a hedge
        ["teapuesto", "miami-heat-vs-boston-celtics", "handicap", "BOS Celtics", None, -4.5, 2.40, None],
    ])
    [opp] = find_opportunities(a, b)
    assert [leg.selection for leg in opp.legs] == ["Celtics -4.5", "Heat +4.5"]


def test_team_totals_compare_the_same_team_only():
    a = book([["pinnacle", "boston-celtics-vs-miami-heat", "total_team", "Boston Celtics", None, 110.5, 2.20, 1.70]])
    b = book([["teapuesto", "miami-heat-vs-boston-celtics", "total_team", "MIA Heat", None, 110.5, 1.70, 2.20]])
    assert find_opportunities(a, b) == []


def test_example_books_end_to_end():
    a = pd.read_csv(EXAMPLES / "pinnacle_nba.csv")
    b = pd.read_csv(EXAMPLES / "teapuesto_nba.csv")
    found = find_opportunities(a, b)
    assert [round(o.roi, 4) for o in found] == [0.0196, 0.0157, 0.0086, 0.0057]
    assert all(o.roi > 0 for o in found)
