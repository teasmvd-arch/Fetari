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

from subtitles import (
    search_movie,
    get_imdb_id,
)

from opensubtitles import (
    search_subtitles,
    get_languages,
    get_releases,
    download_subtitle,
)

from subdl import (
    search_subdl,
    download_subdl,
)

USER_RESULTS = {}

# store download data for buttons
USER_DOWNLOADS = {}

LANGUAGE_NAMES = {
    "en": "🇬🇧 English",
    "fr": "🇫🇷 French",
    "de": "🇩🇪 German",
    "es": "🇪🇸 Spanish",
    "it": "🇮🇹 Italian",
    "pt": "🇵🇹 Portuguese",
    "ar": "🇸🇦 Arabic",
    "tr": "🇹🇷 Turkish",
    "pl": "🇵🇱 Polish",
    "nl": "🇳🇱 Dutch",
    
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome!\n\n"
        "Send me a movie or TV show name.\n\n"
        "Examples:\n"
        "Breaking Bad S01E01\n"
        "Avatar\n"
        "12 Monkeys S02E05"
    )

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    movie_name = update.message.text.strip()

    await update.message.reply_text("🔎 Searching...")
    result = search_movie(movie_name)

    if not result:
        await update.message.reply_text("❌ Movie or TV Show not found.")
        return

    movie = get_imdb_id(
        result["media_type"],
        result["id"],
    )

    if not movie or not movie["imdb_id"]:
        await update.message.reply_text("❌ IMDb ID not found.")
        return

    imdb_id = movie["imdb_id"]

    season = result.get("season")
    episode = result.get("episode")

    opensubs = search_subtitles(
        imdb_id,
        season=season,
        episode=episode,
    )

    subdls = search_subdl(
        imdb_id,
        season=season,
        episode=episode,
    )

    subtitles = opensubs + subdls

    if not subtitles:
        await update.message.reply_text(
            "❌ No subtitles found."
        )
        return

    user_id = update.effective_user.id
   
    USER_RESULTS[user_id] = subtitles

    USER_DOWNLOADS[user_id] = {}

    title = result.get("title") or result.get("name")
    rating = result.get("vote_average", 0)

    year = ""

    if result.get("release_date"):
        year = result["release_date"][:4]
    elif result.get("first_air_date"):
        year = result["first_air_date"][:4]

    poster_url = None

    if result.get("poster_path"):
        poster_url = (
            "https://image.tmdb.org/t/p/w500"
            + result["poster_path"]
        )

    languages = [
        lang
        for lang in get_languages(subtitles)
        if lang in LANGUAGE_NAMES
   ]

    keyboard = []

    for i in range(0, len(languages), 2):

        row = []

        for j in range(2):

            if i + j < len(languages):

                lang = languages[i + j]

                row.append(
                    InlineKeyboardButton(
                        LANGUAGE_NAMES.get(lang, lang),
                        callback_data=f"lang_{lang}",
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
            caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    # ---------- LANGUAGE ----------
    if query.data.startswith("lang_"):

        language = query.data.replace("lang_", "")

        subtitles = USER_RESULTS.get(
            update.effective_user.id,
            [],
        )

        releases = get_releases(subtitles, language)

        keyboard = []
        
        user_id = update.effective_user.id

        for index, release in enumerate(releases):

            key = f"{user_id}_{index}"

            USER_DOWNLOADS[user_id][key] = release

            keyboard.append([
                InlineKeyboardButton(
                    release["release"][:45],
                    callback_data=f"download_{index}",
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="back",
            )
        ])

        await query.edit_message_caption(
            caption=f"{LANGUAGE_NAMES.get(language, language)} Releases",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return

    # ---------- BACK ----------
    if query.data == "back":

        subtitles = USER_RESULTS.get(
            update.effective_user.id,
            [],
        )

        languages = [
            lang
            for lang in get_languages(subtitles)
            if lang in LANGUAGE_NAMES
       ]

        keyboard = []

        for i in range(0, len(languages), 2):

            row = []

            for j in range(2):
                if i + j < len(languages):

                    lang = languages[i + j]

                    row.append(
                        InlineKeyboardButton(
                            LANGUAGE_NAMES.get(lang, lang),
                            callback_data=f"lang_{lang}",
                        )
                    )

            keyboard.append(row)

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return
        
# ---------- DOWNLOAD ----------
if query.data.startswith("download_"):

    user_id = update.effective_user.id

    index = query.data.replace(
        "download_",
        ""
    )

    key = f"{user_id}_{index}"

    release = USER_DOWNLOADS.get(
        user_id,
        {}
    ).get(key)


    if not release:
        await query.message.reply_text(
            "❌ Subtitle not found."
        )
        return


    source = release.get(
        "source",
        "opensubtitles"
    )


    # OpenSubtitles
    if source == "opensubtitles":

        subtitle = download_subtitle(
            release["file_id"]
        )


    # SubDL
    elif source == "subdl":

        subtitle = download_subdl(
            release["download_url"]
        )


    else:

        await query.message.reply_text(
            "❌ Unknown subtitle source."
        )
        return



    if subtitle is None:

        await query.message.reply_text(
            "❌ Download failed."
        )

        return



    subtitle["content"].seek(0)


    await query.message.reply_document(
        document=InputFile(
            subtitle["content"],
            filename=subtitle["filename"],
        ),
        caption="✅ Subtitle downloaded!",
    )

    return


def main():

    check_config()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_callback,
        )
    )

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
