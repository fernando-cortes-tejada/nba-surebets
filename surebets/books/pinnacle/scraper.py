import pandas as pd
from datetime import datetime
from surebets.books import browser as sb_utils
from . import parsing as pi_utils

from .config import INFO


#  scraping function
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
        game_list = pi_utils.get_game_list(driver)
        print(game_list)
        if game_list is None:
            driver.quit()
            return sb_utils.return_info(info)

        # get the list of the matches
        games = pi_utils.get_games_url(game_list)
        print(games)
        if not games:
            driver.quit()
            return sb_utils.return_info(info)

        live_games = pi_utils.get_live_games(driver)
        if live_games:
            games = [game for game in games if game not in live_games]

        # we start iterating over the matches
        for game in games:
            print(game)

            if sb_utils.check_time(t1, timeout, driver):
                return sb_utils.return_info(info)

            # we open the game
            driver.get(game)

            game_name = game.split("/")[-3]
            teams = game_name.split("vs")
            teams = [team.replace("-", " ").strip().lower() for team in teams]

            carousels = pi_utils.get_carousels(driver)
            if not carousels:
                continue

            # we iterate over the carousels
            for carousel in carousels:
                if carousel.text in ["TODO", "GAME PROPS", "GENERAL", "PARTE"]:
                    continue

                if sb_utils.check_time(t1, timeout, driver):
                    return sb_utils.return_info(info)

                carousel.click()

                markets_table = pi_utils.get_markets_table(driver)

                for market_ in markets_table:
                    string = market_.text.split("\n")
                    if len(string) == 1:
                        continue
                    if len(string) == 2 and string[1] == "Ocultar todo":
                        continue

                    if string[-1] == "Más información":
                        pi_utils.more_info(market_)
                        string = market_.text.split("\n")
                        del string[-1]

                    market = string[0]
                    match market:
                        case "Línea de dinero – Partido":
                            market = "winner"
                            info += pi_utils.data_winner(game_name, market, string)
                        case "Hándicap – Partido":
                            market = "handicap"
                            info += pi_utils.data_handicap(
                                game_name, teams, market, string
                            )
                        case "Total – Partido":
                            market = "total"
                            info += pi_utils.data_total(game_name, market, string)
                        case "Total del equipo – Partido":
                            market = "total_team"
                            info += pi_utils.data_total_team(
                                game_name, teams, market, string
                            )
                        case "Línea de dinero – 1.ª parte":
                            market = "winner_first_half"
                            info += pi_utils.data_winner(game_name, market, string)
                        case "Hándicap – 1.ª parte":
                            market = "handicap_first_half"
                            info += pi_utils.data_handicap(
                                game_name, teams, market, string
                            )
                        case "Total – 1.ª parte":
                            market = "total_first_half"
                            info += pi_utils.data_total(game_name, market, string)
                        case "Total del equipo – 1.ª parte":
                            market = "total_team_first_half"
                            info += pi_utils.data_total_team(
                                game_name, teams, market, string
                            )
                        case "Línea de dinero – 1.er cuarto":
                            market = "winner_first_quarter"
                            info += pi_utils.data_winner(game_name, market, string)
                        case "Hándicap – 1.er cuarto":
                            market = "handicap_first_quarter"
                            info += pi_utils.data_handicap(
                                game_name, teams, market, string
                            )
                        case "Total – 1.er cuarto":
                            market = "total_first_quarter"
                            info += pi_utils.data_total(game_name, market, string)
                        case "Total del equipo – 1.er cuarto":
                            market = "total_team_first_quarter"
                            info += pi_utils.data_total_team(
                                game_name, teams, market, string
                            )
                        case "Línea de dinero – 2.º cuarto":
                            market = "winner_second_quarter"
                            info += pi_utils.data_winner(game_name, market, string)
                        case "Hándicap – 2.º cuarto":
                            market = "handicap_second_quarter"
                            info += pi_utils.data_handicap(
                                game_name, teams, market, string
                            )
                        case "Total – 2.º cuarto":
                            market = "total_second_quarter"
                            info += pi_utils.data_total(game_name, market, string)
                        case "Total del equipo – 2.º cuarto":
                            market = "total_team_second_quarter"
                            info += pi_utils.data_total_team(
                                game_name, teams, market, string
                            )

                    if carousel.text == "PLAYER PROPS":
                        if string[1] == "Ocultar todo":
                            del string[1]
                        info += pi_utils.data_players(game_name, market, string)

    except Exception as e:
        print(str(e))

    driver.quit()
    return sb_utils.return_info(info)
