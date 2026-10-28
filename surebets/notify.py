"""Telegram alerts. Without credentials, messages are printed instead."""

import os

import requests


def send_message(message: str, chat_id: str | None = None) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(message)
        return
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message},
        timeout=10,
    )
    response.raise_for_status()
