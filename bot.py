# bot.py
import os
import json
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord import Intents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("valorant-bot")

TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))
FALLBACK_TEXT_CHANNEL_ID = int(os.getenv("FALLBACK_CHANNEL_ID", "0"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", str(15 * 60)))
SOURCE_URL = os.getenv("SOURCE_URL", "https://playvalorant.com/en-us/news/tags/patch-notes/")

STATE_FILE = "state.json"

intents = Intents.default()
client = discord.Client(intents=intents)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"last": ""}
    return {"last": ""}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

async def fetch_latest(session):
    async with session.get(SOURCE_URL, timeout=15) as resp:
        text = await resp.text()
    soup = BeautifulSoup(text, "html.parser")
    item = soup.select_one("a[href*='/en-us/news/']")
    if not item:
        return None
    title = item.get_text(strip=True)
    href = item.get("href")
    link = href if href.startswith("http") else "https://playvalorant.com" + href
    return {"id": link, "title": title, "link": link}

def build_embed(item):
    emb = discord.Embed(title=item["title"], url=item["link"], description="Patch notes terbaru.")
    emb.set_footer(text="Sumber: playvalorant.com")
    return emb

async def post_to_forum_or_text(channel, item):
    embed = build_embed(item)
    try:
        if str(channel.type).lower() == "forum":
            try:
                thread = await channel.create_thread(name=item["title"], content=item["link"])
                return True
            except:
                thread = await channel.create_thread(name=item["title"])
                await thread.send(item["link"], embed=embed)
                return True
        await channel.send(embed=embed)
        return True
    except Exception as e:
        logger.exception(e)
        return False

async def periodic_check():
    await client.wait_until_ready()
    state = load_state()
    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                latest = await fetch_latest(session)
            except Exception as e:
                logger.exception(e)
                latest = None

            if latest and latest["id"] != state.get("last"):
                success = False
                channel = client.get_channel(TARGET_CHANNEL_ID)
                if channel:
                    success = await post_to_forum_or_text(channel, latest)

                if not success and FALLBACK_TEXT_CHANNEL_ID:
                    fallback = client.get_channel(FALLBACK_TEXT_CHANNEL_ID)
                    if fallback:
                        success = await post_to_forum_or_text(fallback, latest)

                if success:
                    state["last"] = latest["id"]
                    save_state(state)

            await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    logger.info(f"Bot ready: {client.user}")

client.loop.create_task(periodic_check())

if __name__ == "__main__":
    if not TOKEN or TARGET_CHANNEL_ID == 0:
        raise SystemExit("Missing DISCORD_TOKEN or TARGET_CHANNEL_ID")
    client.run(TOKEN)
