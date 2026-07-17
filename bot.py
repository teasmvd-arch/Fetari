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
    get_favorites,
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

async def favorites(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = update.effective_user.id

    movies = get_favorites(user_id)


    if not movies:

        await update.message.reply_text(
            "❤️ Your favorites is empty."
        )

        return


    text = "❤️ Your Favorites:\n\n"

    for movie in movies:
        text += f"🎬 {movie[0]}\n"


    await update.message.reply_text(text)

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
        
async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query


    # -------- TITLE --------

    if query.data.startswith("title_"):

        index = int(
            query.data.replace(
                "title_",
                ""
            )
        )

        user_id = update.effective_user.id

        movie = USER_TITLES[user_id][index]


        poster = movie.get("poster")


        title = (
            movie.get("title")
            or movie.get("name")
            or "Unknown"
        )


        if movie.get("release_date"):

            year = movie["release_date"][:4]

        elif movie.get("first_air_date"):

            year = movie["first_air_date"][:4]

        else:

            year = "N/A"


        rating = movie.get(
            "vote_average",
            "N/A"
        )


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
                f"🎬 {title}\n\n"
                f"⭐ Rating: {rating}/10\n"
                f"📅 Year: {year}"
            ),
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )


        imdb = get_imdb_id(
            movie["media_type"],
            movie["id"]
        )


        if not imdb or not imdb.get("imdb_id"):

            await query.message.reply_text(
                "❌ IMDb ID not found."
            )

            return


        await query.message.reply_text(
            "🔎 Searching subtitles..."
        )


        subtitles = (
            search_subtitles(
                imdb["imdb_id"],
                season=movie.get("season"),
                episode=movie.get("episode"),
            )
            +
            search_subdl(
                imdb["imdb_id"],
                season=movie.get("season"),
                episode=movie.get("episode"),
            )
        )


        if not subtitles:

            await query.message.reply_text(
                "❌ No subtitles found."
            )

            return


        USER_RESULTS[user_id] = subtitles


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
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return


           # -------- FAVORITE --------

    if query.data.startswith("fav_"):

        print("FAVORITE CLICKED:", query.data)

        index = int(
            query.data.replace("fav_", "")
        )

        user_id = update.effective_user.id

        movies = USER_TITLES.get(user_id)

        if not movies:
            await query.answer(
                "❌ Please search the movie again.",
                show_alert=True
            )
            return


        movie = movies[index]


        saved = add_favorite(
            user_id,
            {
                "id": movie["id"],
                "title": movie.get("title") or movie.get("name"),
                "poster": movie.get("poster"),
                "media_type": movie.get("media_type"),
            }
        )


        if saved:
            await query.answer(
                "❤️ Added to favorites!",
                show_alert=True
            )
        else:
            await query.answer(
                "❤️ Already saved!",
                show_alert=True
            )

        return
    


    # -------- LANGUAGE --------

    if query.data.startswith("lang_"):

        language = query.data.replace(
            "lang_",
            ""
        )

        user_id = update.effective_user.id


        subtitles = USER_RESULTS.get(
            user_id,
            []
        )


        releases = get_releases(
            subtitles,
            language
        )


        if not releases:

            await query.message.reply_text(
                "❌ No releases found."
            )

            return


        USER_DOWNLOADS[user_id] = {}


        keyboard = []


        for index, release in enumerate(releases):

            key = str(index)

            USER_DOWNLOADS[user_id][key] = release


            keyboard.append(
                [
                    InlineKeyboardButton(
                        release.get(
                            "release",
                            "Subtitle"
                        )[:45],
                        callback_data=f"download_{index}"
                    )
                ]
            )


        keyboard.append(
            [
                InlineKeyboardButton(
                    "⬅ Back",
                    callback_data="back"
                )
            ]
        )


        await query.edit_message_text(
            text=(
                f"{LANGUAGE_NAMES.get(language, language)} Releases"
            ),
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )


        return



    # -------- DOWNLOAD --------

    if query.data.startswith("download_"):

        index = query.data.replace(
            "download_",
            ""
        )


        user_id = update.effective_user.id


        release = USER_DOWNLOADS.get(
            user_id,
            {}
        ).get(index)


        if not release:

            await query.message.reply_text(
                "❌ Subtitle not found."
            )

            return



        source = release.get(
            "source",
            "opensubtitles"
        )


        if source == "opensubtitles":

            subtitle = download_subtitle(
                release["file_id"]
            )


        elif source == "subdl":

            subtitle = download_subdl(
                release["download_url"]
            )


        else:

            subtitle = None



        if not subtitle:

            await query.message.reply_text(
                "❌ Download failed."
            )

            return



        subtitle["content"].seek(0)


        await query.message.reply_document(
            document=InputFile(
                subtitle["content"],
                filename=subtitle["filename"]
            ),
            caption="✅ Subtitle downloaded!"
        )


        return



    # -------- BACK --------

    if query.data == "back":

        await query.edit_message_text(
            "🌍 Choose subtitle language again."
        )

        return
            
             
def main():

    check_config()

    init_db()

    app = Application.builder().token(
        BOT_TOKEN
    ).build()


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            button_callback
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search
        )
    )


    print("🤖 Bot is running...")


    app.run_polling()



if __name__ == "__main__":
    main()
