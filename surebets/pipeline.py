"""Airflow task callables: notify -> scrape each book -> compare -> clean up.

Scraped odds are written to CSV between tasks because each Airflow task
runs in its own process; the files are deleted at the end of every run.
"""

from datetime import datetime
from itertools import combinations
import os
from pathlib import Path

import pandas as pd

from surebets.alerts import format_alert
from surebets.books import get_scraper
from surebets.matching import find_opportunities
from surebets.notify import send_message

DATA_DIR = Path(os.getenv("SUREBETS_DATA_DIR", "data"))
MIN_ROI = float(os.getenv("SUREBETS_MIN_ROI", "0.0"))
# keep each leg modest: books limit accounts that keep betting their maximum
MAX_STAKE = float(os.getenv("SUREBETS_MAX_STAKE", "50"))


def _path(website: str, league: str) -> Path:
    return DATA_DIR / f"{website}_{league}.csv"


def trigger(league: str, websites: list[str], **_) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_message(f"Scraping {', '.join(websites)} ({league.upper()}) at {now}")


def scrape(league: str, website: str, timeout: int, attempts: int = 2, **_) -> None:
    """Scrape one book, retrying once if it comes back empty."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame()
    for _attempt in range(attempts):
        try:
            df = get_scraper(website)(league, timeout)
        except Exception as e:  # a broken page must not stop the other books
            send_message(f"{website} ({league.upper()}) failed: {e}")
            continue
        if len(df) > 0:
            break
    send_message(f"{website} ({league.upper()}): {len(df)} odds")
    df.to_csv(_path(website, league), index=False)


def calculate(league: str, websites: list[str], **_) -> None:
    books = {}
    for website in websites:
        path = _path(website, league)
        if path.exists() and path.stat().st_size > 0:
            books[website] = pd.read_csv(path)

    found = []
    for a, b in combinations(books, 2):
        found += find_opportunities(books[a], books[b], min_roi=MIN_ROI)

    if not found:
        send_message(f"No surebets ({league.upper()})")
        return
    send_message(f"Found {len(found)} surebets ({league.upper()})")
    for opp in sorted(found, key=lambda o: o.roi, reverse=True):
        send_message(format_alert(opp, MAX_STAKE))


def clean(league: str, **_) -> None:
    for path in DATA_DIR.glob(f"*_{league}.csv"):
        path.unlink()
