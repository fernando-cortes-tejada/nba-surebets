"""Format an opportunity as the message sent to Telegram."""

from surebets.arbitrage import capped_stakes
from surebets.markets import MARKET_LABELS
from surebets.matching import Opportunity


def format_alert(opp: Opportunity, max_stake: float, increment: float = 0.1) -> str:
    stakes, profit = capped_stakes([leg.odds for leg in opp.legs], max_stake, increment)
    market = MARKET_LABELS.get(opp.market, opp.market.replace("_", " "))
    player = opp.player.title() if opp.player else None
    subject = " · ".join(x for x in (opp.game, player, opp.team, market) if x)
    show_line = opp.line is not None and not opp.market.startswith(("winner", "handicap"))
    line = f" {opp.line:g}" if show_line else ""
    legs = "\n".join(
        f"  {leg.book}: {leg.selection} @ {leg.odds:.2f} -> stake {stake:.2f}"
        for leg, stake in zip(opp.legs, stakes)
    )
    return (
        f"ARB {opp.roi:+.2%}  {subject}{line}\n{legs}\n"
        f"  locked profit {profit:+.2f} on {sum(stakes):.2f} staked\n"
        "  re-check both prices before placing: books correct within ~30s"
    )
