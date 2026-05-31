import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip().strip('"').strip("'")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip().strip('"').strip("'")

client = Groq(api_key=GROQ_API_KEY)

chats = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я AI-ассистент. Задай любой вопрос 👋")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вот что я умею:\n\n"
        "/start — начать разговор\n"
        "/reset — очистить историю чата\n"
        "/help — список команд\n\n"
        "Просто напиши мне любой вопрос и я отвечу!"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.pop(update.effective_chat.id, None)
    await update.message.reply_text("История очищена! Начинаем с чистого листа.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if chat_id not in chats:
        chats[chat_id] = []

    chats[chat_id].append({"role": "user", "content": user_text})
    chats[chat_id] = chats[chat_id][-20:]

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты полезный ассистент в Telegram. Отвечай на русском языке, кратко и понятно."},
                *chats[chat_id]
            ],
            max_tokens=1024,
        )
        reply = response.choices[0].message.content
        chats[chat_id].append({"role": "assistant", "content": reply})

    except Exception as e:
        reply = "Произошла ошибка. Попробуй ещё раз."
        print(f"Ошибка: {e}")

    await update.message.reply_text(reply)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()


main()