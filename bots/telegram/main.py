import os
import logging

from urllib.parse import urljoin

import requests

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, ApplicationBuilder, filters

PORT = int(os.environ["PORT"])
BOT_TOKEN = os.environ["BOT_TOKEN"]
APPNAME = os.environ["APPNAME"]
RANKIE_GAME_RESULTS_URL = os.environ.get("RANKIE_GAME_RESULTS_URL")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger()


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text="Oops, something is broken...")


async def send_game_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Got update: %s" % update)
    logger.info("Got args: %s" % context.args)
    chat_id = update.message.chat_id

    message = update.message.text
    username = update.message.from_user.username

    if message.startswith("Wordle"):
        game_label = "wordle_eng"
    elif "Wordle (RU)" in message:
        game_label = "wordle_ru"
    elif message.startswith("Reversle"):
        game_label = "reversle_eng"
    elif message.startswith("nerdlegame"):
        game_label = "nerdle"
    else:
        await context.bot.send_message(chat_id=chat_id, text="Sorry, I can't guess the game name")
        return

    data = {"player": username, "game": game_label, "origin": "TG_BOT", "text": message}
    response = requests.post(RANKIE_GAME_RESULTS_URL, json=data)

    if response.status_code != 201:
        logger.error(f"Status code: {response.status_code}, Text: {response.text}")
        reason = "API error"
        if response.text and "must make a unique set" in response.text:
            reason = "already registered"

        await context.bot.send_message(chat_id=chat_id, text=f"Failed to send game result: {reason}")
        return

    game_result_id = response.json()["id"]
    register_url = urljoin(RANKIE_GAME_RESULTS_URL, str(game_result_id) + "/register/")
    response = requests.get(register_url)

    if response.status_code != 200:
        logger.error(f"Status code: {response.status_code}, Text: {response.text}")
        reason = "API error"
        await context.bot.send_message(chat_id=chat_id, text=f"Failed to register game result: {reason}")
        return

    await context.bot.send_message(chat_id=chat_id, text="Game result was successfully sent and registered")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)
    app.add_handler(
        MessageHandler(
            filters=filters.TEXT & filters.ChatType.PRIVATE & (~filters.UpdateType.EDITED), callback=send_game_result
        )
    )
    app.run_webhook(
        listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN, webhook_url=f"https://{APPNAME}.herokuapp.com/{BOT_TOKEN}"
    )


if __name__ == "__main__":
    main()
