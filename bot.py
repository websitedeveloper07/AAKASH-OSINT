import logging
import requests
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters, ContextTypes
from cookies import cookies, headers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ASK_PSID_PIC, ASK_PSID_INFO = range(2)

# -------- Start Command -------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼 PSID → Pic", callback_data="psid_pic")],
        [InlineKeyboardButton("ℹ️ PSID → Info", callback_data="psid_info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "╔════════════════════╗\n"
        "  👋 **Welcome to Aakash OSINT Bot**\n"
        "╚════════════════════╝\n\n"
        "🔎 *Uses of this bot:*\n"
        "• Get profile picture from PSID\n"
        "• Get user information from PSID\n\n"
        "👉 Choose an option below:"
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# -------- Callback Buttons -------- #
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "psid_pic":
        await query.message.reply_text("🖼 Please send me the *PSID* for picture lookup:", parse_mode="Markdown")
        return ASK_PSID_PIC
    elif query.data == "psid_info":
        await query.message.reply_text("ℹ️ Please send me the *PSID* for info lookup:", parse_mode="Markdown")
        return ASK_PSID_INFO

# -------- PSID to Pic -------- #
async def psid_to_pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"http://aakashleap.com:3131/Content/ScoreToolImage/{psid}.jpg"

    caption = (
        "╔════════════════════╗\n"
        f"   🖼 *Picture for PSID:* `{psid}`\n"
        "╚════════════════════╝"
    )

    try:
        await update.message.reply_photo(photo=url, caption=caption, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not fetch picture for `{psid}`\nError: {e}", parse_mode="Markdown")

    return ConversationHandler.END

# -------- PSID to Info -------- #
async def psid_to_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"https://learn.aakashitutor.com/api/getuserinfo?auth=true&email={psid}@aesl.in"

    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        data = response.json()

        if not data or not isinstance(data, list):
            await update.message.reply_text("❌ No data found for this PSID.")
            return ConversationHandler.END

        user = data[0]

        # Convert timestamp → human readable date
        created_ts = int(user.get("created", 0))
        created_date = datetime.datetime.fromtimestamp(created_ts).strftime("%d-%m-%Y %H:%M:%S") if created_ts else "N/A"

        info_text = (
            "📌 *My Aakash OSINT search results:*\n\n"
            "```\n"
            f"👤 Name       : {user.get('title', 'N/A')}\n"
            f"📧 Email      : {user.get('email', 'N/A')}\n"
            f"📱 Mobile     : {user.get('mobile', 'N/A')}\n"
            f"🆔 UID        : {user.get('uid', 'N/A')}\n"
            f"🔑 Username   : {user.get('sso_username', 'N/A')}\n"
            f"🎓 Role       : {', '.join(user.get('roles', {}).values()) if user.get('roles') else 'N/A'}\n"
            f"📅 Created    : {created_date}\n"
            f"🏷 Firstname  : {user.get('firstname', 'N/A')}\n"
            f"🏷 Lastname   : {user.get('lastname', 'N/A')}\n"
            "```"
        )

        await update.message.reply_text(info_text, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching info for `{psid}`\nError: {e}", parse_mode="Markdown")

    return ConversationHandler.END

# -------- Main -------- #
def main():
    application = Application.builder().token("8252385992:AAFrqTjKwWrRQtC2ZX4RmtNObgayecDHAZw").build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            ASK_PSID_PIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_pic)],
            ASK_PSID_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_info)],
        },
        fallbacks=[],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
