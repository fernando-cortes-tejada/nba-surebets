"""Sportsbook scrapers, all exposed as `scrape(league, timeout) -> DataFrame`.

Pinnacle and Teapuesto cover game markets and player props; Betano and
Chúntala (the 2023 version of the system) scrape player props one
category at a time, so they are wrapped to loop over the categories.

These scrapers read live page structure and break whenever a site
changes its markup; they are kept as a reference for how the data was
collected. `python -m surebets.demo` runs the engine on sample data.
"""

from datetime import datetime

import pandas as pd

from surebets.markets import DF_COLS

# Betano's scraper predates the shared English column names
_BETANO_COLUMNS = {
    "casa": "website",
    "mercado": "market",
    "equipo": "team",
    "jugador": "player",
    "linea": "line",
    "mas": "more",
    "menos": "less",
}


def _by_category(scrape, categories, website):
    def run(league: str, timeout: int) -> pd.DataFrame:
        frames = []
        for category in categories:
            start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            frames.append(scrape(league, category, start, timeout))
        df = pd.concat(frames, ignore_index=True).rename(columns=_BETANO_COLUMNS)
        df["website"] = website
        return df.reindex(columns=DF_COLS)

    return run


def get_scraper(website: str):
    """Import lazily so the engine and tests do not need Selenium."""
    match website:
        case "pinnacle":
            from surebets.books.pinnacle.scraper import scrape
        case "teapuesto":
            from surebets.books.teapuesto.scraper import scrape
        case "betano":
            from surebets.books.betano.config import INFO
            from surebets.books.betano.scraper import scrape as by_category

            scrape = _by_category(by_category, INFO["nba"]["category"], website)
        case "chuntala":
            from surebets.books.chuntala.config import INFO
            from surebets.books.chuntala.scraper import scrape as by_category

            scrape = _by_category(by_category, INFO["nba"]["category"], website)
        case _:
            raise ValueError(f"unknown sportsbook: {website}")
    return scrape


BOOKS = ("pinnacle", "teapuesto", "betano", "chuntala")
