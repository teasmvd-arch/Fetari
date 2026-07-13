from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, check_config
from subtitles import search_movie, get_imdb_id
from opensubtitles import (
    search_subtitles,
    download_subtitle,
)

USER_RESULTS = {}

LANGUAGE_NAMES = {
    "en": "🇬🇧 English",
    "fr": "🇫🇷 French",
    "de": "🇩🇪 German",
    "es": "🇪🇸 Spanish",
    "it": "🇮🇹 Italian",
    "pt": "🇵🇹 Portuguese",
    "pt-BR": "🇧🇷 Portuguese (Brazil)",
    "pt-PT": "🇵🇹 Portuguese (Portugal)",
    "ar": "🇸🇦 Arabic",
    "tr": "🇹🇷 Turkish",
    "ko": "🇰🇷 Korean",
    "ja": "🇯🇵 Japanese",
    "ru": "🇷🇺 Russian",
    "pl": "🇵🇱 Polish",
    "nl": "🇳🇱 Dutch",
    "ro": "🇷🇴 Romanian",
    "vi": "🇻🇳 Vietnamese",
    "hi": "🇮🇳 Hindi",
    "zh-CN": "🇨🇳 Chinese",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome!\n\n"
        "Send me a movie or TV show name."
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text.strip()

    await update.message.reply_text("🔎 Searching...")

    result = search_movie(movie_name)

    if not result:
        await update.message.reply_text("❌ Movie not found.")
        return

    imdb_id = get_imdb_id(
        result["media_type"],
        result["id"],
    )

    if not imdb_id:
        await update.message.reply_text("❌ IMDb ID not found.")
        return

    subtitles = search_subtitles(imdb_id)

    USER_RESULTS[update.effective_user.id] = subtitles

    if not subtitles:
        await update.message.reply_text("❌ No subtitles found.")
        return

    title = result.get("title") or result.get("name")
    rating = result.get("vote_average", 0)

    year = ""
    if result.get("release_date"):
        year = result["release_date"][:4]
    elif result.get("first_air_date"):
        year = result["first_air_date"][:4]

    poster_path = result.get("poster_path")
    poster_url = None

    if poster_path:
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

    keyboard = []

    for i in range(0, min(len(subtitles), 20), 2):
        row = []

        for j in range(2):
            if i + j < min(len(subtitles), 20):
                sub = subtitles[i + j]

                row.append(
                    InlineKeyboardButton(
                        LANGUAGE_NAMES.get(
                            sub["language"],
                            sub["language"],
                        ),
                        callback_data=f"download_{sub['file_id']}",
                    )
                )

        keyboard.append(row)

    caption = (
        f"🎬 {title}\n"
        f"⭐ {rating:.1f}/10\n"
        f"📅 {year}\n\n"
        f"Choose subtitle language:"
    )

    if poster_url:
        await update.message.reply_photo(
            photo=poster_url,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.message.reply_text(
            text=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    file_id = query.data.replace("download_", "")

    await query.edit_message_caption(
        caption="📥 Downloading subtitle..."
    )

    subtitle = download_subtitle(file_id)

    if subtitle is None:
        await query.message.reply_text(
            "❌ Failed to download subtitle."
        )
        return

    subtitle.name = "subtitle.srt"

    await query.message.reply_document(
        document=InputFile(subtitle),
        filename="subtitle.srt",
        caption="✅ Subtitle downloaded successfully!"
    )

    try:
        await query.delete_message()
    except Exception:
        pass


def main():
    check_config()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search,
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
