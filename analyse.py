import os
import asyncio
from dotenv import load_dotenv
from apify_client import ApifyClientAsync
import telegram

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")

INSTAGRAM_ACCOUNTS = [
    # Deutsch
    "taliamenzel",
    "tina_schwarz.lipoedem_talk",
    "lipoedemkeinproblem",
    "mama_undmeer",
    "judithsendl",
    "belanda.feelgood",
    "zuckerfreierlei",
    # Englisch
    "lipedema.coach",
    "the_lippy_lady",
    "lipedemasociety",
    "mylipedemajourney",
    "lipedemafitness",
    "lipedema_uplifted",
]

TOP_N = 5


def engagement_score(post):
    views = post.get("videoViewCount") or 0
    likes = post.get("likesCount") or 0
    comments = post.get("commentsCount") or 0
    if views > 0:
        return views + likes + comments * 5
    return likes + comments * 5


async def scrape_account(client, username):
    run_input = {
        "usernames": [username],
        "resultsLimit": 50
    }
    run = await client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
    items = []
    async for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        items.append(item)
    return items[0] if items else None


async def send_message(bot, text):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)


async def main():
    client = ApifyClientAsync(APIFY_TOKEN)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    await send_message(bot, "📊 Wöchentliche Top-Content Analyse startet...")

    for username in INSTAGRAM_ACCOUNTS:
        print(f"Analysiere @{username}...")
        profile = await scrape_account(client, username)

        if not profile:
            print(f"Kein Profil für @{username}")
            continue

        posts = profile.get("latestPosts", [])
        if not posts:
            continue

        sorted_posts = sorted(posts, key=engagement_score, reverse=True)
        top_posts = sorted_posts[:TOP_N]

        lines = [f"🏆 Top {TOP_N} — @{username}\n"]
        for i, post in enumerate(top_posts, 1):
            views = post.get("videoViewCount")
            likes = post.get("likesCount") or 0
            comments = post.get("commentsCount") or 0
            caption = (post.get("caption") or "")[:100]
            url = post.get("url", "")

            stats = f"{views:,} Views" if views else f"{likes:,} Likes"
            stats += f" | {comments:,} Kommentare"

            lines.append(f"{i}. {stats}")
            lines.append(f"   {caption or 'Kein Text'}...")
            if url:
                lines.append(f"   {url}")

        await send_message(bot, "\n".join(lines))
        await asyncio.sleep(1)

    await send_message(bot, "✅ Analyse abgeschlossen.")
    print("Fertig!")


if __name__ == "__main__":
    asyncio.run(main())
