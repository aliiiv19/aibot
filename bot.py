import os
import httpx
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Загружаем ключи из .env
load_dotenv()

# Отключаем системный прокси чтобы не мешал
os.environ.pop("ALL_PROXY", None)
os.environ.pop("all_proxy", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("HTTP_PROXY", None)

# Подключаемся к Gemini
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# История чатов
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

    # Добавляем сообщение пользователя в историю
    chats[chat_id].append({"role": "user", "parts": [{"text": user_text}]})

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=chats[chat_id],
        )
        reply = response.text

        # Сохраняем ответ в историю
        chats[chat_id].append({"role": "model", "parts": [{"text": reply}]})

    except Exception as e:
        reply = "Произошла ошибка. Попробуй ещё раз."
        print(f"Ошибка: {e}")

    await update.message.reply_text(reply)


def main():
    # Создаём бота без системного прокси
    app = (
        ApplicationBuilder()
        .token(os.environ["BOT_TOKEN"])
        .proxy(None)
        .get_updates_proxy(None)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен! Нажми Ctrl+C чтобы остановить.")
    app.run_polling()


main()