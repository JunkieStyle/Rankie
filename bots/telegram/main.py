import os
import logging

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
        game_label = "wordle"
        game_round = int(message.split()[1])
    else:
        await context.bot.send_message(chat_id=chat_id, text="Sorry, I can't guess the game name")
        return

    data = {"user": username, "game": game_label, "round": game_round, "origin": "TG_BOT", "text": message}
    response = requests.post(RANKIE_GAME_RESULTS_URL, json=data)
    if response.status_code == 201:
        await context.bot.send_message(
            chat_id=chat_id, text=f"Result successfully registered, game '{game_label}, round {game_label}"
        )
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"Failed result registration for game '{game_label}'")


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
