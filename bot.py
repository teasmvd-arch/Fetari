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

from database import (
    init_db,
    add_favorite,
)


USER_TITLES = {}
USER_RESULTS = {}
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

    results = search_movie(movie_name)

    user_id = update.effective_user.id

    USER_TITLES[user_id] = results


    if not results:

        await update.message.reply_text(
            "❌ Movie or TV Show not found."
        )

        return


    keyboard = []


    for index, item in enumerate(results[:10]):

        title = (
            item.get("title")
            or item.get("name")
            or "Unknown"
        )


        if item.get("release_date"):

            year = item["release_date"][:4]

        elif item.get("first_air_date"):

            year = item["first_air_date"][:4]

        else:

            year = "----"


        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🎬 {title} ({year})",
                    callback_data=f"title_{index}",
                )
            ]
        )


    await update.message.reply_text(
        "🎬 Choose a title:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
        
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()
    
    # ---------- ADD FAVORITE ----------
    if query.data.startswith("fav_"):

        index = int(query.data.replace("fav_", ""))

        user_id = update.effective_user.id

        movie = USER_TITLES[user_id][index]

        saved = add_favorite(
            user_id,
            {
                "id": movie["id"],
                "title": movie.get("title") or movie.get("name"),
                "poster": movie.get("poster_path"),
                "media_type": movie.get("media_type")
            }
        )

        if saved:
            await query.answer("❤️ Added to favorites!")
        else:
            await query.answer("Already saved!")

        return

# ---------- TITLE CLICK ----------
if query.data.startswith("title_"):

    index = int(query.data.replace("title_", ""))
    user_id = update.effective_user.id

    movie = USER_TITLES[user_id][index]

    poster_path = movie.get("poster_path")

    if poster_path:
        poster = (
            "https://image.tmdb.org/t/p/w500"
            + poster_path
        )
    else:
        poster = "https://via.placeholder.com/500x750"


    keyboard = [
        [
            InlineKeyboardButton(
                "❤️ Add Favorite",
                callback_data=f"fav_{index}"
            )
        ]
    ]


    await query.message.reply_photo(
        photo=poster,
        caption=(
            f"🎬 {movie.get('title') or movie.get('name')}\n"
            f"⭐ Rating: {movie.get('vote_average', 'N/A')}\n"
            f"📅 Year: {movie.get('release_date', movie.get('first_air_date', 'N/A'))[:4]}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


    media_type = movie["media_type"]
    tmdb_id = movie["id"]

    season = movie.get("season")
    episode = movie.get("episode")


    imdb = get_imdb_id(
        media_type,
        int(tmdb_id)
    )


    if not imdb or not imdb.get("imdb_id"):

        await query.message.reply_text(
            "❌ IMDb ID not found."
        )
        return


    imdb_id = imdb["imdb_id"]


    await query.message.reply_text(
        "🔎 Searching subtitles..."
    )


    opensubs = search_subtitles(
        imdb_id,
        season=season,
        episode=episode
    )


    subdls = search_subdl(
        imdb_id,
        season=season,
        episode=episode
    )


    subtitles = opensubs + subdls


    if not subtitles:

        await query.message.reply_text(
            "❌ No subtitles found."
        )
        return


    USER_RESULTS[user_id] = subtitles

    USER_DOWNLOADS[user_id] = {}


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

                lang = languages[i+j]

                row.append(
                    InlineKeyboardButton(
                        LANGUAGE_NAMES[lang],
                        callback_data=f"lang_{lang}"
                    )
                )

        keyboard.append(row)


    await query.message.reply_text(
        "🌍 Choose subtitle language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


    return
        
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

        await query.edit_message_text(
          text=f"{LANGUAGE_NAMES.get(language, language)} Releases",
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


        # OpenSubtitles download
        if source == "opensubtitles":

            subtitle = download_subtitle(
                release["file_id"]
            )


        # SubDL download
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

    init_db()

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
