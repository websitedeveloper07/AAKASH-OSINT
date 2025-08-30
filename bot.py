import os
import logging
import httpx
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from cookies import cookies

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
ASK_PSID_PIC, ASK_PSID_INFO = range(2)


# -------- Helper: Box -------- #
def box(content: str) -> str:
    return f"┏━━━━━━━⍟\n┃ {content}\n┗━━━━━━━━━━━⊛"


# -------- Start Command -------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼 PSID → Pic", callback_data="psid_pic")],
        [InlineKeyboardButton("ℹ️ PSID → Info", callback_data="psid_info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "👋 *Welcome to Aakash OSINT Bot*\n\n"
        "🔎 *Uses of this bot:*\n"
        "• Get profile picture from PSID\n"
        "• Get user information from PSID\n\n"
        "👉 Choose an option below:"
    )

    await update.message.reply_text(
        welcome_text, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


# -------- Callback Buttons -------- #
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "psid_pic":
        await query.message.reply_text(
            box("🖼 Please send me the *PSID* for picture lookup:"),
            parse_mode="MarkdownV2",
        )
        return ASK_PSID_PIC

    elif query.data == "psid_info":
        await query.message.reply_text(
            box("ℹ️ Please send me the *PSID* for info lookup:"),
            parse_mode="MarkdownV2",
        )
        return ASK_PSID_INFO


# -------- PSID → Picture -------- #
async def psid_to_pic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"http://aakashleap.com:3131/Content/ScoreToolImage/{psid}.jpg"

    caption = (
        "┏━━━━━━━⍟\n"
        "┃ 🖼 *My Aakash OSINT Picture:*\n"
        "┗━━━━━━━━━━━⊛\n\n"
        f"🆔 PSID: `{psid}`"
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                await update.message.reply_photo(
                    photo=resp.content, caption=caption, parse_mode="MarkdownV2"
                )
            else:
                await update.message.reply_text(
                    box(f"❌ No valid picture found for `{psid}`"),
                    parse_mode="MarkdownV2",
                )
    except Exception as e:
        await update.message.reply_text(
            box(f"❌ Could not fetch picture for `{psid}`\nError: `{e}`"),
            parse_mode="MarkdownV2",
        )

    return ConversationHandler.END


# -------- PSID → Info -------- #
async def psid_to_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    psid = update.message.text.strip()
    url = f"https://learn.aakashitutor.com/api/getuserinfo?auth=true&email={psid}@aesl.in"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, cookies=cookies, timeout=15)
            data = resp.json()

        if not data or not isinstance(data, list):
            await update.message.reply_text(
                "```\n❌ No data found for this PSID.\n```",
                parse_mode="MarkdownV2",
            )
            return ConversationHandler.END

        user = data[0]

        # Convert timestamp → human readable date
        created_ts = int(user.get("created", 0))
        created_date = (
            datetime.datetime.fromtimestamp(created_ts).strftime("%d-%m-%Y %H:%M:%S")
            if created_ts
            else "N/A"
        )

        # Handle roles properly
        roles = user.get("roles")
        if isinstance(roles, dict):
            roles_text = ", ".join(roles.values())
        elif isinstance(roles, list):
            roles_text = ", ".join(roles)
        else:
            roles_text = "N/A"

        # Build info text inside backticks
        info_text = (
            "```\n"
            "┏━━━━━━━⍟\n"
            "┃ 📌 My Aakash OSINT Results:\n"
            "┗━━━━━━━━━━━⊛\n\n"
            f"👤 Name       : {user.get('title', 'N/A')}\n"
            f"📧 Email      : {user.get('email', 'N/A')}\n"
            f"📱 Mobile     : {user.get('mobile', 'N/A')}\n"
            f"🆔 UID        : {user.get('uid', 'N/A')}\n"
            f"🎓 Role       : {roles_text}\n"
            f"📅 Created    : {created_date}\n"
            f"🏷 Firstname  : {user.get('firstname', 'N/A')}\n"
            f"🏷 Lastname   : {user.get('lastname', 'N/A')}\n"
            "```"
        )

        await update.message.reply_text(info_text, parse_mode="MarkdownV2")

    except Exception as e:
        await update.message.reply_text(
            f"```\n┏━━━━━━━⍟\n┃ ❌ Error fetching info for {psid}\n┃ Error: {e}\n┗━━━━━━━━━━━⊛\n```",
            parse_mode="MarkdownV2",
        )

    return ConversationHandler.END



# -------- Main -------- #
def main():
    TOKEN = os.getenv("BOT_TOKEN")  # keep token safe in env var
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN not set in environment variables")

    application = Application.builder().token(TOKEN).build()

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

    logger.info("✅ Bot started...")
    application.run_polling()


if __name__ == "__main__":
    main()
