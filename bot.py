import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)
from cookies import cookies

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States
PSID_TO_PIC, PSID_TO_INFO = range(2)


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼 PSID → Pic", callback_data="psid_pic")],
        [InlineKeyboardButton("📑 PSID → Info", callback_data="psid_info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome = (
        "╔══════════════════╗\n"
        "║   🔎 Welcome to Aakash OSINT Bot   ║\n"
        "╚═══════════════════════╝\n\n"
        "Choose an option below 👇"
    )

    await update.message.reply_text(welcome, reply_markup=reply_markup)


# Handle menu clicks
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "psid_pic":
        await query.message.reply_text("🖼 Send me the PSID to fetch the picture:")
        return PSID_TO_PIC

    elif query.data == "psid_info":
        await query.message.reply_text("📑 Send me the PSID to fetch the info:")
        return PSID_TO_INFO


# PSID → Pic
async def psid_to_pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"http://aakashleap.com:3131/Content/ScoreToolImage/Output{psid}.jpg"

    caption = (
        "╔════════════════════════════╗\n"
        f"║   🖼 Picture for PSID: `{psid}`   ║\n"
        "╚════════════════════════════╝"
    )

    try:
        await update.message.reply_photo(photo=url, caption=caption, parse_mode="Markdown")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Could not fetch picture (maybe PSID invalid).")

    return ConversationHandler.END


# PSID → Info
async def psid_to_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"https://learn.aakashitutor.com/api/getuserinfo?auth=true&email={psid}@aesl.in"

    try:
        response = requests.get(url, cookies=cookies)
        if response.ok and response.text.strip() != "[]":
            user = response.json()[0]

            created_ts = user.get("created")
            created_date = (
                datetime.utcfromtimestamp(int(created_ts)).strftime("%d-%m-%Y %H:%M:%S")
                if created_ts else "N/A"
            )

            info = (
                "╔════════════════════╗\n"
                "║   📑 My Aakash OSINT Search Results   \n"
                "╚══════════════════════════╝\n\n"
                f"👤 Name: `{user.get('title', 'N/A')}`\n"
                f"📧 Email: `{user.get('email', 'N/A')}`\n"
                f"📱 Mobile: `{user.get('mobile', 'N/A')}`\n"
                f"🆔 UID: `{user.get('uid', 'N/A')}`\n"
                f"🎓 Role: `{', '.join(user.get('roles', {}).values()) if user.get('roles') else 'N/A'}`\n"
                f"🆔 Username: `{user.get('sso_username', 'N/A')}`\n"
                f"📅 Created: `{created_date}`\n"
                f"🏷️ Firstname: `{user.get('firstname', 'N/A')}`\n"
                f"🏷️ Lastname: `{user.get('lastname', 'N/A')}`\n"
            )

            await update.message.reply_text(info, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No info found (maybe cookies expired).")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("⚠️ Error fetching user info.")

    return ConversationHandler.END


# Main
def main():
    app = Application.builder().token("8252385992:AAFrqTjKwWrRQtC2ZX4RmtNObgayecDHAZw").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PSID_TO_PIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_pic)],
            PSID_TO_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_info)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(menu_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
