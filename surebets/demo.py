"""Run the matching engine on sample odds, no browser needed.

    python -m surebets.demo [book_a.csv book_b.csv]
"""

from pathlib import Path
import sys

import pandas as pd

from surebets.alerts import format_alert
from surebets.matching import find_opportunities

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def main(argv: list[str]) -> None:
    paths = argv or [EXAMPLES / "pinnacle_nba.csv", EXAMPLES / "teapuesto_nba.csv"]
    a, b = (pd.read_csv(p) for p in paths)
    found = find_opportunities(a, b)
    print(f"{len(a)} + {len(b)} odds scanned, {len(found)} arbitrages\n")
    for opp in found:
        print(format_alert(opp, max_stake=50), end="\n\n")


if __name__ == "__main__":
    main(sys.argv[1:])
