import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = "8858472917:AAFjcWl4Gdc6CgZ_nYDqiF3QoIBrViPtcsc"
ADMIN_ID = 408203815

SCHEDULE = {
    "sat": {"day": "Субота", "time": "14:00", "date_label": "найближча субота"},
    "sun": {"day": "Неділя", "time": "14:00", "date_label": "найближча неділя"},
}
PRICE = 400

WAITING_NAME, WAITING_PEOPLE, WAITING_CORP_CONTACT = range(3)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Записатись на гру", callback_data="book")],
        [InlineKeyboardButton("📅 Розклад та ціни", callback_data="info")],
        [InlineKeyboardButton("🏢 Корпоратив / приватна подія", callback_data="corp")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
    ])


def schedule_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Субота 14:00", callback_data="book_sat")],
        [InlineKeyboardButton("📅 Неділя 14:00", callback_data="book_sun")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="start")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Головне меню", callback_data="start")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"Привіт, {user.first_name}! 🃏\n\n"
        "Ласкаво просимо до <b>Secret Mafia 1329</b>\n"
        "Мафія в Києві, яку хочеться проживати знову\n\n"
        "Як я можу допомогти?"
    )
    if update.message:
        await update.message.reply_html(text, reply_markup=main_menu_keyboard())
    else:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start":
        await start(update, context)

    elif data == "info":
        text = (
            "📅 <b>Розклад ігор:</b>\n"
            "• Субота — 14:00\n"
            "• Неділя — 14:00\n\n"
            "💰 <b>Ціна:</b> 400 грн/особа\n\n"
            "🎭 <b>Що включено:</b>\n"
            "• Ведучий пояснює правила\n"
            "• 3–4 партії за вечір\n"
            "• Блеф, емоції, нові знайомства\n\n"
            "Новачкам завжди раді — досвід не потрібен!"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Записатись", callback_data="book")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="start")],
        ])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)

    elif data == "book":
        text = (
            "🗓 <b>Оберіть зручний день:</b>\n\n"
            "📅 Субота — 14:00\n"
            "📅 Неділя — 14:00\n\n"
            f"💰 Ціна: {PRICE} грн/особа"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=schedule_keyboard())

    elif data in ("book_sat", "book_sun"):
        slot = "sat" if data == "book_sat" else "sun"
        context.user_data["slot"] = slot
        day = SCHEDULE[slot]["day"]
        time = SCHEDULE[slot]["time"]
        text = (
            f"Чудово! Ви обрали <b>{day} {time}</b>\n\n"
            "Введіть ваше <b>ім'я</b>:"
        )
        await query.edit_message_text(text, parse_mode="HTML")
        return WAITING_NAME

    elif data == "corp":
        text = (
            "🏢 <b>Корпоративи та приватні події</b>\n\n"
            "Мафія для команд від 12 до 30+ людей\n\n"
            "✅ Ведучі\n"
            "✅ Організація під ключ\n"
            "✅ Корпоративи та тімбілдінги\n"
            "✅ Дні народження та особливі події\n\n"
            "Напишіть ваш контакт (ім'я + телефон або Telegram), "
            "і ми зв'яжемось найближчим часом:"
        )
        await query.edit_message_text(text, parse_mode="HTML")
        return WAITING_CORP_CONTACT

    elif data == "faq":
        text = (
            "❓ <b>Часті питання:</b>\n\n"
            "<b>Чи потрібно вміти грати?</b>\n"
            "Ні! Ведучий пояснює правила перед грою.\n\n"
            "<b>Скільки людей бере участь?</b>\n"
            "Від 8 до 15 гравців за столом.\n\n"
            "<b>Де ви знаходитесь?</b>\n"
            "Київ. Точну адресу надсилаємо після підтвердження запису.\n\n"
            "<b>Чи є знижки?</b>\n"
            "Так, для груп від 5 осіб — уточнюйте у адміністратора.\n\n"
            "<b>Скільки триває вечір?</b>\n"
            "Зазвичай 3–4 години."
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_keyboard())


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_html(
        f"Дякую, <b>{context.user_data['name']}</b>!\n\n"
        "Скільки людей прийде? Введіть кількість (наприклад: <b>2</b>):"
    )
    return WAITING_PEOPLE


async def get_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("Будь ласка, введіть число людей (наприклад: 2):")
        return WAITING_PEOPLE

    people = int(text)
    context.user_data["people"] = people
    slot = context.user_data["slot"]
    name = context.user_data["name"]
    day = SCHEDULE[slot]["day"]
    time = SCHEDULE[slot]["time"]
    total = people * PRICE

    confirm_text = (
        f"✅ <b>Заявку прийнято!</b>\n\n"
        f"👤 Ім'я: {name}\n"
        f"📅 День: {day} {time}\n"
        f"👥 Кількість: {people} особа(и)\n"
        f"💰 Сума: {total} грн\n\n"
        "Адміністратор підтвердить запис найближчим часом.\n"
        "⏰ Нагадаємо за 2 години до гри!"
    )
    await update.message.reply_html(confirm_text, reply_markup=main_menu_keyboard())

    admin_text = (
        f"🆕 <b>Нова заявка на гру!</b>\n\n"
        f"👤 Ім'я: {name}\n"
        f"📅 День: {day} {time}\n"
        f"👥 Кількість: {people} особа(и)\n"
        f"💰 Сума: {total} грн\n"
        f"🆔 Telegram ID: {update.effective_user.id}\n"
        f"👤 Username: @{update.effective_user.username or 'немає'}"
    )
    await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")

    # Нагадування за 2 години до гри
    now = datetime.now()
    weekday = now.weekday()
    if slot == "sat":
        days_ahead = (5 - weekday) % 7
    else:
        days_ahead = (6 - weekday) % 7
    if days_ahead == 0:
        days_ahead = 7
    game_dt = (now + timedelta(days=days_ahead)).replace(hour=14, minute=0, second=0, microsecond=0)
    remind_dt = game_dt - timedelta(hours=2)
    delay = (remind_dt - now).total_seconds()

    if delay > 0:
        context.job_queue.run_once(
            send_reminder,
            when=delay,
            data={"chat_id": update.effective_user.id, "name": name, "day": day, "time": time},
            name=f"reminder_{update.effective_user.id}"
        )

    return ConversationHandler.END


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    text = (
        f"⏰ <b>Нагадування!</b>\n\n"
        f"{data['name']}, через 2 години ваша гра!\n"
        f"📅 {data['day']} о {data['time']}\n\n"
        "Чекаємо вас! 🃏"
    )
    await context.bot.send_message(data["chat_id"], text, parse_mode="HTML")


async def get_corp_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text.strip()
    user = update.effective_user

    await update.message.reply_html(
        "✅ Дякуємо! Ваш запит передано адміністратору.\n"
        "Очікуйте на зв'язок найближчим часом 🙌",
        reply_markup=main_menu_keyboard()
    )

    admin_text = (
        f"🏢 <b>Запит на корпоратив!</b>\n\n"
        f"👤 Від: {user.first_name} (@{user.username or 'немає'})\n"
        f"🆔 ID: {user.id}\n"
        f"📞 Контакт: {contact}"
    )
    await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^book_(sat|sun)$"),
                      CallbackQueryHandler(button_handler, pattern="^corp$")],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            WAITING_PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_people)],
            WAITING_CORP_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_corp_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Бот запущено!")
    app.run_polling()


if __name__ == "__main__":
    main()
