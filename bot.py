import requests
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)

# States
ASK_PSID_PIC, ASK_PSID_INFO = range(2)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("PSID to Pic", callback_data="psid_pic"),
            InlineKeyboardButton("PSID to Info", callback_data="psid_info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to the bot!\n\n"
        "This bot helps you with:\n"
        "- Converting PSID to Picture\n"
        "- Fetching Info using PSID\n\n"
        "Choose an option below:",
        reply_markup=reply_markup
    )

# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "psid_pic":
        await query.edit_message_text("📷 Please send me the PSID to get the picture.")
        return ASK_PSID_PIC
    elif query.data == "psid_info":
        await query.edit_message_text("ℹ️ Please send me the PSID to get the info.")
        return ASK_PSID_INFO

# PSID → Pic (fixed with BytesIO)
async def psid_to_pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"http://aakashleap.com:3131/Content/ScoreToolImage/Output{psid}.jpg"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("image"):
            image_bytes = BytesIO(response.content)
            image_bytes.name = f"{psid}.jpg"

            await update.message.reply_photo(photo=image_bytes, caption=f"Here is the picture for PSID: {psid}")
        else:
            await update.message.reply_text("❌ No valid image found for this PSID.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error fetching picture: {e}")

    return ConversationHandler.END

# PSID → Info
async def psid_to_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    api_url = f"https://learn.aakashitutor.com/api/getuserinfo?auth=true&email={psid}@aesl.in"

    try:
        response = requests.get(api_url, timeout=10)
        data = response.json()

        if not data:
            await update.message.reply_text("❌ No info found for this PSID.")
            return ConversationHandler.END

        user = data[0]

        # Clean fields we want to display
        info = (
            f"👤 Name: {user.get('title', 'N/A')}\n"
            f"📧 Email: {user.get('email', 'N/A')}\n"
            f"📱 Mobile: {user.get('mobile', 'N/A')}\n"
            f"🎓 Role: {', '.join(user.get('roles', {}).values()) if user.get('roles') else 'N/A'}\n"
            f"🆔 Username: {user.get('sso_username', 'N/A')}\n"
            f"📅 Created: {user.get('created', 'N/A')}\n"
            f"🏷️ Firstname: {user.get('firstname', 'N/A')}\n"
            f"🏷️ Lastname: {user.get('lastname', 'N/A')}\n"
        )

        await update.message.reply_text(info)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error fetching info: {e}")

    return ConversationHandler.END

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# Main
def main():
    TOKEN = "8252385992:AAFrqTjKwWrRQtC2ZX4RmtNObgayecDHAZw"  # Your Bot Token
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),
                      CallbackQueryHandler(button_handler)],
        states={
            ASK_PSID_PIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_pic)],
            ASK_PSID_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, psid_to_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
