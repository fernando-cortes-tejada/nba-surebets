import pandas as pd
from surebets.books import browser as sb_utils
from . import parsing as ta_utils
from datetime import datetime

from .config import INFO


# teapuesto scraping function
def scrape(league: str, timeout: int) -> pd.DataFrame:
    t1 = datetime.now()

    # get the url to scrape
    url = INFO.get(league).get("url")

    info = []

    # prod = True means that the browser will be headless
    driver = sb_utils.initiate_driver(prod=True)
    sb_utils.open_browser(driver, url, 0)

    try:
        # we get the list of the matches (separated by days)
        game_list = ta_utils.get_game_list(driver)
        if game_list is None:
            driver.quit()
            return sb_utils.return_info(info)

        # we get the days of the matches
        days = ta_utils.get_days(game_list)
        if days is None:
            driver.quit()
            return sb_utils.return_info(info)

        # get the list of the matches
        games = ta_utils.get_games(days)
        if games is None:
            driver.quit()
            return sb_utils.return_info(info)

        # we start iterating over the matches
        for j in range(0, len(games)):
            if sb_utils.check_time(t1, timeout, driver):
                return sb_utils.return_info(info)

            # we get the list of the matches (separated by days)
            game_list = ta_utils.get_game_list(driver)
            if game_list is None:
                continue

            # we get the days of the matches
            days = ta_utils.get_days(game_list)
            if days is None:
                continue

            # get the list of the matches
            games = ta_utils.get_games(days)

            # click on the match
            print(f"Te Apuesto: Partido {j+1} de {len(games)}")
            click_game_bool = ta_utils.click_game(games[j])

            # if the click on the match opened it, continue the scraping
            if click_game_bool:
                carousels = ta_utils.get_carousels(driver)
                if not carousels:
                    continue

                if sb_utils.check_time(t1, timeout, driver):
                    return sb_utils.return_info(info)

                game_name = ta_utils.get_game_name(driver)
                teams = [
                    team.strip().lower()
                    for team in game_name.replace("-", " ").split("vs")
                ]

                # we iterate over the carousels
                for carousel in carousels:
                    # we click if we are not in the first carousel
                    if "Apuestas Generales" not in carousel.text:
                        carousel.click()

                    markets_table = ta_utils.get_markets_table(driver)

                    for market_ in markets_table:
                        string = market_.split("\n")

                        market = string[0]
                        market = market.split("(")[0].strip()

                        match market:
                            case "Ganador":
                                market = "winner"
                                info += ta_utils.data_winner(
                                    game_name, teams, market, string
                                )
                            case "Total":
                                market = "total"
                                info += ta_utils.data_total(game_name, market, string)
                            case "Hándicap":
                                market = "handicap"
                                info += ta_utils.data_handicap(
                                    game_name, teams, market, string
                                )
                            case "1 total" | "home total" | "Local total":
                                market = "total_team"
                                info += ta_utils.data_total_team(
                                    game_name, teams[0], market, string
                                )
                            case "2 total" | "away total" | "Visitante total":
                                market = "total_team"
                                info += ta_utils.data_total_team(
                                    game_name, teams[1], market, string
                                )
                            case "1º Mitad - hándicap":
                                market = "handicap_first_half"
                                info += ta_utils.data_handicap(
                                    game_name, teams, market, string
                                )
                            case "1st half - total":
                                market = "total_first_half"
                                info += ta_utils.data_total(game_name, market, string)
                            case "1er cuarto - hándicap":
                                market = "handicap_first_quarter"
                                info += ta_utils.data_handicap(
                                    game_name, teams, market, string
                                )
                            case "2do cuarto - hándicap":
                                market = "handicap_second_quarter"
                                info += ta_utils.data_handicap(
                                    game_name, teams, market, string
                                )

                if j == len(games) - 1:
                    driver.quit()
                    return sb_utils.return_info(info)

                driver.get(url)

    except Exception as e:
        print(str(e))

    driver.quit()
    return sb_utils.return_info(info)
