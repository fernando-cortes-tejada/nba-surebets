"""Selenium helpers shared by the scrapers."""

from datetime import datetime
import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from surebets.markets import CHROMEDRIVER_PATH, DF_COLS

os.environ["webdriver.chrome.driver"] = CHROMEDRIVER_PATH


def initiate_driver(prod: bool = True) -> webdriver.Chrome:
    """Chrome driver; `prod=True` runs headless."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    if prod:
        options.add_argument("--window-size=1420,1080")
        options.add_argument("--headless")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)


def open_browser(driver: webdriver.Chrome, url: str, time_sleep: int) -> None:
    driver.get(url)
    time.sleep(time_sleep)


def check_time(t1: datetime, timeout: int, driver: webdriver.Chrome) -> bool:
    """Quit the driver and return True once `timeout` seconds have passed."""
    if (datetime.now() - t1).seconds > timeout:
        print("timeout")
        driver.quit()
        return True
    return False


def return_info(info: list) -> pd.DataFrame:
    return pd.DataFrame.from_dict(info) if info else pd.DataFrame(columns=DF_COLS)
