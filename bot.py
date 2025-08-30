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

# PSID → Pic
async def psid_to_pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"http://aakashleap.com:3131/Content/ScoreToolImage/Output{psid}.jpg"

    await update.message.reply_photo(photo=url, caption=f"Here is the picture for PSID: {psid}")
    return ConversationHandler.END

# PSID → Info (placeholder, update with real API if you have)
async def psid_to_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    await update.message.reply_text(f"ℹ️ Info for PSID {psid} (API integration can be added here).")
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
