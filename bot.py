#Telegram bot. Set the BOT_TOKEN environment variable, then run: python bot.py
import io
import os

from PIL import Image
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from scam_core import read_image_text, summary


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Paste a job or skills ad, or send a screenshot, "
        "and I'll check it for scam red flags."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(summary(update.message.text))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    tg_file = await photo.get_file()
    data = await tg_file.download_as_bytearray()
    text = read_image_text(Image.open(io.BytesIO(bytes(data))))
    if not text:
        await update.message.reply_text(
            "I couldn't read text from that image. Try pasting the text instead."
        )
        return
    await update.message.reply_text(summary(text))


def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("Set the BOT_TOKEN environment variable first.")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()


if __name__ == "__main__":
    main()