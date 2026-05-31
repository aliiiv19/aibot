import os
import asyncio
from groq import Groq
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip().strip('"').strip("'")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip().strip('"').strip("'")

client = Groq(api_key=GROQ_API_KEY)

chats = {}
modes = {}

MODES = {
    "🤖 Ассистент": "Ты полезный ассистент в Telegram. Отвечай на русском языке, кратко и понятно.",
    "👨‍💻 Программист": "Ты опытный программист. Помогай с кодом, объясняй ошибки, предлагай решения. Отвечай на русском языке.",
    "🌍 Переводчик": "Ты профессиональный переводчик. Переводи текст на нужный язык. Если язык не указан — переводи на английский.",
    "🧠 Психолог": "Ты внимательный психолог. Выслушивай, поддерживай и давай советы. Отвечай на русском языке, мягко и с пониманием.",
    "😂 Юморист": "Ты весёлый comedian. Отвечай с юмором, шути и поднимай настроение. Отвечай на русском языке.",
}

DEFAULT_MODE = "🤖 Ассистент"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я AI-ассистент. Задай любой вопрос 👋\n\n"
        "Используй /mode чтобы сменить режим работы."
    )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вот что я умею:\n\n"
        "/start — начать разговор\n"
        "/reset — очистить историю чата\n"
        "/mode — сменить режим работы\n"
        "/help — список команд\n\n"
        "Просто напиши мне любой вопрос и я отвечу!"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.pop(update.effective_chat.id, None)
    modes.pop(update.effective_chat.id, None)
    # Удаляем сообщение пользователя с командой /reset
    await update.message.delete()
    # Отправляем уведомление и удаляем его через 3 секунды
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✅ История очищена!"
    )
    await asyncio.sleep(3)
    await msg.delete()


async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[m] for m in MODES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Выбери режим работы:",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    # Проверяем выбрал ли пользователь режим
    if user_text in MODES:
        modes[chat_id] = user_text
        chats.pop(chat_id, None)
        await update.message.reply_text(f"Режим изменён на {user_text}! История очищена.")
        return

    if chat_id not in chats:
        chats[chat_id] = []

    chats[chat_id].append({"role": "user", "content": user_text})
    chats[chat_id] = chats[chat_id][-20:]

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Берём system prompt текущего режима
    current_mode = modes.get(chat_id, DEFAULT_MODE)
    system_prompt = MODES[current_mode]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
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
    app.add_handler(CommandHandler("mode", mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()


main()