import os
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip().strip('"').strip("'")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip().strip('"').strip("'")

print(f"BOT_TOKEN длина: {len(BOT_TOKEN)}")
print(f"GEMINI_API_KEY длина: {len(GEMINI_API_KEY)}")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY не найден!")

client = genai.Client(api_key=GEMINI_API_KEY)

chats = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я AI-ассистент на базе Gemini. Задай любой вопрос 👋")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.pop(update.effective_chat.id, None)
    await update.message.reply_text("История очищена! Начинаем с чистого листа.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if chat_id not in chats:
        chats[chat_id] = []

    chats[chat_id].append({"role": "user", "parts": [{"text": user_text}]})

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=chats[chat_id],
        )
        reply = response.text
        chats[chat_id].append({"role": "model", "parts": [{"text": reply}]})

    except Exception as e:
        reply = "Произошла ошибка. Попробуй ещё раз."
        print(f"Ошибка: {e}")

    await update.message.reply_text(reply)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()


main()