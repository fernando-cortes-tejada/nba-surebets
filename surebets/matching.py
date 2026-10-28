"""Line up the same bet across two sportsbooks and find arbitrages.

Each book's scraper returns rows with the columns in `markets.DF_COLS`.
Books name teams, players and markets differently, so rows are normalized
to shared keys before joining:

* game:   order-independent pair of team nicknames ("celtics-vs-heat")
* team:   nickname ("Celtics")
* market: canonical market name (see `markets.DICT_BETANO_CHUNTALA`)
* player: accent-insensitive name, fuzzy-matched across books

Three kinds of market are compared:

* over/under (game totals, team totals, player props): over on one book
  against under on the other, at the same line
* handicap: team X at line L on one book against team Y at -L on the other
* winner (moneyline): team X on one book against team Y on the other
"""

from dataclasses import dataclass
import difflib
import unicodedata

import pandas as pd

from surebets import arbitrage
from surebets.markets import DICT_BETANO_CHUNTALA, DICT_NBA_TEAMS, PLAYER_PROP_MARKETS


@dataclass(frozen=True)
class Leg:
    book: str
    selection: str
    odds: float


@dataclass(frozen=True)
class Opportunity:
    game: str | None
    market: str
    team: str | None
    player: str | None
    line: float | None
    legs: tuple[Leg, ...]

    @property
    def roi(self) -> float:
        return arbitrage.guaranteed_return([leg.odds for leg in self.legs])

    def stakes(self, bankroll: float) -> list[float]:
        return arbitrage.optimal_stakes([leg.odds for leg in self.legs], bankroll)


def _value(v):
    """NaN from missing CSV cells -> None."""
    return None if v is None or (isinstance(v, float) and v != v) else v


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def nickname(team: str | None) -> str | None:
    """'LAL Lakers' / 'Los Angeles Lakers' -> 'Lakers'."""
    if not isinstance(team, str) or not team.strip():
        return None
    team = DICT_NBA_TEAMS.get(team.strip(), team.strip())
    # "Trail Blazers" is the only two-word nickname in the league
    if team.lower().endswith("trail blazers"):
        return "Trail Blazers"
    return team.split()[-1].capitalize()


def game_key(game: str | None) -> str | None:
    """'boston-celtics-vs-miami-heat' and 'miami-heat-vs-boston-celtics'
    both become 'celtics-vs-heat', so home/away order does not matter."""
    if not isinstance(game, str) or "-vs-" not in game:
        return None
    teams = [side.strip("-").split("-")[-1].lower() for side in game.split("-vs-")]
    return "-vs-".join(sorted(teams))


def player_key(player: str | None) -> str | None:
    if not isinstance(player, str) or not player.strip():
        return None
    return " ".join(_strip_accents(player).lower().replace(".", "").split())


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ("website", "game", "team", "player", "line", "more", "less"):
        if col not in out:
            out[col] = None
    out["market"] = out["market"].map(lambda m: DICT_BETANO_CHUNTALA.get(m, m))
    out["game"] = out["game"].map(game_key)
    out["team"] = out["team"].map(nickname)
    out["player"] = out["player"].map(player_key)
    out["line"] = pd.to_numeric(out["line"], errors="coerce")
    return out


def align_players(flawed: pd.Series, reference: pd.Series, cutoff: float = 0.85) -> pd.Series:
    """Map each name in `flawed` to its closest name in `reference`
    ("luka doncic" vs "luka dončić jr"), leaving unmatched names as they are."""
    names = [n for n in reference.unique() if isinstance(n, str)]

    def best(name):
        if not isinstance(name, str) or name in names:
            return name
        match = difflib.get_close_matches(name, names, n=1, cutoff=cutoff)
        return match[0] if match else name

    return flawed.map(best)


def _kind(market: str) -> str:
    if market in PLAYER_PROP_MARKETS:
        return "player_prop"
    if market.startswith("winner"):
        return "winner"
    if market.startswith("handicap"):
        return "handicap"
    return "total"  # total, total_first_half, total_team, ...


def _over_under(a: pd.DataFrame, b: pd.DataFrame, keys: list[str]) -> list[Opportunity]:
    df = a.merge(b, on=keys, suffixes=("_a", "_b"))
    found = []
    for row in df.itertuples(index=False):
        r = row._asdict()
        for side_a, side_b in (("more", "less"), ("less", "more")):
            oa, ob = r[f"{side_a}_a"], r[f"{side_b}_b"]
            if pd.isna(oa) or pd.isna(ob) or oa <= 1 or ob <= 1:
                continue
            label = {"more": "over", "less": "under"}
            found.append(
                Opportunity(
                    game=_value(r.get("game") if "game" in keys else r.get("game_a")),
                    market=r["market"],
                    team=_value(r.get("team")) if "team" in keys else None,
                    player=_value(r.get("player")) if "player" in keys else None,
                    line=_value(r["line"]),
                    legs=(
                        Leg(r["website_a"], label[side_a], float(oa)),
                        Leg(r["website_b"], label[side_b], float(ob)),
                    ),
                )
            )
    return found


def _two_teams(a: pd.DataFrame, b: pd.DataFrame, handicap: bool) -> list[Opportunity]:
    b = b.copy()
    if handicap:
        # team X -4.5 on book A is covered by team Y +4.5 on book B
        b["line"] = -b["line"]
    keys = ["game", "market"] + (["line"] if handicap else [])
    df = a.merge(b, on=keys, suffixes=("_a", "_b"))
    df = df[df["team_a"].notna() & df["team_b"].notna() & (df["team_a"] != df["team_b"])]
    found = []
    for row in df.itertuples(index=False):
        r = row._asdict()
        oa, ob = r["more_a"], r["more_b"]
        if pd.isna(oa) or pd.isna(ob) or oa <= 1 or ob <= 1:
            continue
        line = r["line"] if handicap else None
        found.append(
            Opportunity(
                game=r["game"],
                market=r["market"],
                team=None,
                player=None,
                line=line,
                legs=(
                    Leg(r["website_a"], f"{r['team_a']}" + (f" {line:+g}" if handicap else ""), float(oa)),
                    Leg(r["website_b"], f"{r['team_b']}" + (f" {-line:+g}" if handicap else ""), float(ob)),
                ),
            )
        )
    return found


def find_opportunities(
    book_a: pd.DataFrame, book_b: pd.DataFrame, min_roi: float = 0.0
) -> list[Opportunity]:
    """All cross-book arbitrages between two scraped books, best first."""
    a, b = normalize(book_a), normalize(book_b)
    if a.empty or b.empty:
        return []
    b["player"] = align_players(b["player"], a["player"])
    a["kind"] = a["market"].map(_kind)
    b["kind"] = b["market"].map(_kind)

    def part(kind):
        return a[a["kind"] == kind].drop(columns="kind"), b[b["kind"] == kind].drop(columns="kind")

    found: list[Opportunity] = []
    # a player is in one game per night, so props match without the game key
    # (some books do not expose it on the prop page)
    found += _over_under(*part("player_prop"), keys=["market", "player", "line"])
    ta, tb = part("total")
    team_totals = ta["market"].str.startswith("total_team")
    found += _over_under(ta[~team_totals], tb[~tb["market"].str.startswith("total_team")], keys=["game", "market", "line"])
    found += _over_under(ta[team_totals], tb[tb["market"].str.startswith("total_team")], keys=["game", "market", "team", "line"])
    found += _two_teams(*part("handicap"), handicap=True)
    found += _two_teams(*part("winner"), handicap=False)

    found = [o for o in found if o.roi > min_roi]
    return sorted(found, key=lambda o: o.roi, reverse=True)
