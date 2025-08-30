import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Import cookies
from cookies import cookies

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for ConversationHandler
ASK_PSID_PIC, ASK_PSID_INFO = range(2)

# Headers for API
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36"
}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("PSID to Pic 📷", callback_data="psid_pic")],
        [InlineKeyboardButton("PSID to Info ℹ️", callback_data="psid_info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to Aakash OSINT Bot!\n\nChoose an option below:",
        reply_markup=reply_markup,
    )

# Handle button clicks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "psid_pic":
        await query.message.reply_text("📸 Please send the PSID to get the picture:")
        return ASK_PSID_PIC

    elif query.data == "psid_info":
        await query.message.reply_text("ℹ️ Please send the PSID to get the info:")
        return ASK_PSID_INFO

# PSID → Pic
async def psid_to_pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"http://aakashleap.com:3131/Content/ScoreToolImage/Output{psid}.jpg"

    try:
        # Validate if image exists
        resp = requests.get(url, stream=True)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
            await update.message.reply_photo(photo=url, caption=f"Here is the picture for PSID: {psid}")
        else:
            await update.message.reply_text("❌ No picture found for this PSID.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("⚠️ Error fetching the picture.")

    return ConversationHandler.END

# PSID → Info
async def psid_to_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"https://learn.aakashitutor.com/api/getuserinfo?auth=true&email={psid}@aesl.in"

    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        if response.ok and response.text.strip() != "[]":
            data = response.json()[0]

            # Ignore groups/ids and show main info
            info = (
                f"👤 Name: {data.get('title', 'N/A')}\n"
                f"📧 Email: {data.get('email', 'N/A')}\n"
                f"📱 Mobile: {data.get('mobile', 'N/A')}\n"
                f"🆔 UID: {data.get('uid', 'N/A')}\n"
                f"🎓 Role: {list(data.get('roles', {}).values())[0] if data.get('roles') else 'N/A'}\n"
                f"🗓 Created: {data.get('created', 'N/A')}\n"
            )
            await update.message.reply_text(info)
        else:
            await update.message.reply_text("❌ No info found (maybe cookies expired?).")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("⚠️ Error fetching user info.")

    return ConversationHandler.END

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

def main():
    # Replace with your Bot Token
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button)],
        states={
            ASK_PSID_PIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_pic)],
            ASK_PSID_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
