from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time
import pandas as pd
import re
import math
from datetime import datetime

from surebets.markets import DICT_NBA_TEAMS, DICT_BETANO_CHUNTALA, DF_COLS


def get_game_list(driver: webdriver.Chrome, timeout: int = 20) -> WebElement | None:
    t1 = datetime.now()
    t2 = datetime.now()
    while (t2 - t1).seconds < timeout:
        try:
            game_list = driver.find_element(
                by=By.CLASS_NAME, value="market-table.ng-star-inserted"
            )
        except:
            pass
        else:
            print("game list ok")
            return game_list

    print("game list not found")
    return None


def get_days(game_list: webdriver.Chrome, timeout: int = 20) -> list | None:
    t1 = datetime.now()
    t2 = datetime.now()
    while (t2 - t1).seconds < timeout:
        try:
            days = game_list.find_elements(
                by=By.XPATH,
                value="//*[starts-with(@class, 'group-events-table')]",
            )
        except:
            pass
        else:
            print(f"Te apuesto: {len(days)} days found")
            return days

    print("Te apuesto: days not found")
    return None


def get_games(days: list[WebElement]) -> list | None:
    def find_games(day: WebElement) -> list[WebElement]:
        return day.find_elements(by=By.CLASS_NAME, value="overflow-ellipsis")

    try:
        for day in days:
            if "games" in locals():
                games += find_games(day)
            else:
                games = find_games(day)
    except:
        print("Te Apuesto: games not found")
        return None
    else:
        games = games[1::2]
        print(f"Te apuesto: {len(games)} games found")
        return games


def click_game(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    t1 = datetime.now()
    t2 = datetime.now()
    while (t2 - t1).seconds < timeout:
        try:
            driver.click()
        except:
            pass
        else:
            print("game ok")
            return True

    print("game not found")
    return False


def get_carousels(driver: webdriver.Chrome, timeout: int = 10) -> list | None:
    t1 = datetime.now()
    t2 = datetime.now()
    while (t2 - t1).seconds < timeout:
        try:
            carousels = driver.find_element(
                by=By.CLASS_NAME, value="nav.nav-tabs"
            ).find_elements(
                by=By.XPATH, value="//*[contains(@class, 'nav-item ng-star-inserted')]"
            )
            carousels = [carousel for carousel in carousels if carousel.text != ""]
        except:
            pass
        else:
            print(f"Te apuesto: {len(carousels)} carousels found")
            return carousels

    print("Carousels not found")
    return None


def click_carousel(carrusel: webdriver.Chrome, time_sleep: int = 1) -> bool:
    try:
        carrusel.click()
        print(f"Te apuesto: carousel {carrusel.text} ok")
    except Exception as e:
        print(e)
        print("Te apuesto: carousel not found")
        return False
    else:
        time.sleep(time_sleep)
        return True


def get_game_name(driver: webdriver.Chrome) -> str | None:
    try:
        game_name = (
            driver.find_element(
                by=By.XPATH, value="//li[starts-with(@class, 'team-name')]"
            )
            .text.lower()
            .replace(" ", "-")
        )
    except:
        print("Te apuesto: game name not found")
        return None
    else:
        print(f"Te apuesto: game name {game_name} ok")
        return game_name


def get_markets_table(
    driver: webdriver.Chrome, timeout: int = 10
) -> list[WebElement] | None:
    t1 = datetime.now()
    t2 = datetime.now()
    while (t2 - t1).seconds < timeout:
        try:
            markets_table = driver.find_elements(
                by=By.XPATH,
                value="//nvscore-accordion[starts-with(@class, 'extra-odds-accordion-container')]",
            )
        except:
            pass
        else:
            markets_table = [
                market_.text for market_ in markets_table if market_.text != ""
            ]
            print(f"Te apuesto: {len(markets_table)} markets found")
            return markets_table

    print("Te apuesto: markets table not found")
    return None


def data_winner(game_name: str, teams: str, market: str, string: list) -> list:
    info = []
    string = string[1:]
    for i in range(2):
        data_ = string[(i * 2) + 1]
        info += [
            {
                "website": "teapuesto",
                "game": game_name,
                "market": market,
                "team": teams[i],
                "more": float(data_),
            }
        ]
    return info


def data_total(game_name: str, market: str, string: list) -> list:
    string = string[-4:]

    info = [
        {
            "website": "teapuesto",
            "game": game_name,
            "market": market,
            "line": float(string[0].split(" ")[-1]),
            "more": float(string[1]),
            "less": float(string[3]),
        }
    ]
    return info


def data_handicap(game_name: str, teams: list, market: str, string: list) -> list:
    string = string[1:]

    info = [
        {
            "website": "teapuesto",
            "game": game_name,
            "market": market,
            "team": teams[0],
            "line": float(string[0].split(" ")[-1].replace("(", "").replace(")", "")),
            "more": float(string[1]),
            "less": float(string[3]),
        }
    ]
    return info


def data_total_team(game_name: str, team: str, market: str, string: list) -> list:
    string = string[1:]

    info = [
        {
            "website": "teapuesto",
            "game": game_name,
            "market": market,
            "team": team,
            "line": float(string[0].split(" ")[-1]),
            "more": float(string[1]),
            "less": float(string[3]),
        }
    ]
    return info


def close_game(driver: webdriver.Chrome, timeout: int = 5) -> None:
    t1 = datetime.now()
    t2 = datetime.now()
    while (t2 - t1).seconds < timeout:
        try:
            boton = driver.find_element(
                by=By.XPATH,
                value="//button[starts-with(@class, 'btn-modal-close')]",
            ).find_element(by=By.XPATH, value="//span[starts-with(@class, 'ng-tns')]")
            action = webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element_with_offset(boton, 600, 300)
            action.click()
            action.perform()
        except:
            pass
        else:
            print("Te apuesto: close game ok")
            return None

    print("Close game not found")
    return None


def get_plays(driver: webdriver.Chrome) -> tuple:
    try:
        plays = driver.find_elements(
            by=By.CLASS_NAME,
            value="style__Header-sc-s6lgwx-5.hOzuiU.market-collapse",
        )
        odds = driver.find_elements(
            by=By.CLASS_NAME,
            value="style__Body-sc-s6lgwx-6.cIJRCQ.markets__body-container",
        )
    except:
        print("Te apuesto: plays not found")
        return None, None
    else:
        print(f"Te apuesto: {len(plays)} plays found")
        return plays, odds


def get_player(string: str) -> str:
    return string[0 : (string.find("(") - 1)]


def get_team(string: str) -> str:
    return DICT_NBA_TEAMS.get(
        string[(string.find("(") + 1) : (string.find(")"))],
        string[(string.find("(") + 1) : (string.find(")"))],
    )


def get_market(string: str) -> str:
    return DICT_BETANO_CHUNTALA.get(
        string[(string.find(")") + 2) : (string.find("\n"))],
        string[(string.find(")") + 2) : (string.find("\n"))],
    )


def get_line(string: str) -> float:
    line = string.split("\n")[-4].split(" ")[-1].replace("(", "").replace(")", "")
    return float(line)


def get_info(string: str) -> dict:
    info = {
        "player": get_player(string),
        "team": get_team(string),
        "market": get_market(string),
        "line": get_line(string),
        "more": float(string.split("\n")[-3]),
        "less": float(string.split("\n")[-1]),
    }
    return info


def get_alt_info(string: str) -> list:
    info = []
    for l in range(int((len(string.split("\n")) - 1) / 2)):
        player = string.split("\n")[(2 * l) + 1]
        team = ""
        market = DICT_BETANO_CHUNTALA.get(
            string.split("\n")[0].split(" ")[-1],
            string.split("\n")[0].split(" ")[-1],
        )
        line = float(re.findall(r"\b\d+\b", string.split("\n")[0])[0]) - 0.5
        more = float(string.split("\n")[(2 * l) + 2])
        less = math.nan

        dict_ = {
            "website": "teapuesto",
            "market": market,
            "team": team,
            "player": player,
            "line": line,
            "more": more,
            "less": less,
        }
        info += [dict_]
    return info


def get_linea_mlb(string: str, mercado: str) -> float:
    if mercado == "Jonrones":
        linea = 0.5
    else:
        valor = re.findall(r"\d+", string.split("\n")[0])
        if valor:
            linea = float(valor[0]) - 0.5
        else:
            linea = 0.5
    return float(linea)


def get_mlb_info(string: str) -> list:
    info = []
    for m in range(int((len(string.split("\n")) - 1) / 2)):
        player = string.split("\n")[(2 * m) + 1]
        team = ""
        market = DICT_BETANO_CHUNTALA.get(string.split("\n")[0])
        line = get_linea_mlb(string, market)
        more = float(string.split("\n")[(2 * m) + 2])
        less = math.nan

        dict_ = {
            "website": "teapuesto",
            "market": market,
            "team": team,
            "player": player,
            "line": line,
            "more": more,
            "less": less,
        }
        info += [dict_]
    return info


def check_time(dt_ini: str, timeout: int, driver: webdriver.Chrome) -> bool:
    dt_fin = datetime.now()
    if (dt_fin - datetime.strptime(dt_ini, "%Y-%m-%d %H:%M:%S")).seconds > timeout:
        print("Chuntala: timeout")
        driver.quit()
        return True
    else:
        return False


def return_info(info: list) -> pd.DataFrame:
    if info:
        return pd.DataFrame.from_dict(info)
    else:
        return pd.DataFrame(columns=DF_COLS)


def get_plays_str(play, odd) -> str | None:
    try:
        string = play.text + "\n" + odd.text
    except:
        string = None
        print("Chuntala: play string not found")
    return string
