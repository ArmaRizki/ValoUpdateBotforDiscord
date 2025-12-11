import os
import json
import requests
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("WEBHOOK")  # set in GitHub Secrets as "WEBHOOK"
STATE_FILE = "state.json"
URL = "https://playvalorant.com/en-us/news/tags/patch-notes/"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"last": ""}
    return {"last": ""}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def fetch_latest():
    resp = requests.get(URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Note: PlayValorant HTML structure may change.
    # The selector below attempts to find the first news item link.
    item = soup.select_one("a[href*='/en-us/news/']")
    if not item:
        return None

    title = item.get_text(strip=True)
    href = item.get('href')
    if href.startswith("http"):
        link = href
    else:
        link = "https://playvalorant.com" + href

    return {"id": link, "title": title, "link": link}

def send_discord(item):
    if not WEBHOOK:
        print("WEBHOOK not set")
        return False

    payload = {
        "username": "Valorant Updates",
        "embeds": [
            {
                "title": item["title"],
                "url": item["link"],
                "description": "Patch notes / announcement terbaru — klik link untuk detail.",
                "footer": {"text": "Sumber: playvalorant.com"}
            }
        ]
    }

    r = requests.post(WEBHOOK, json=payload, timeout=10)
    try:
        r.raise_for_status()
        return True
    except Exception as e:
        print("Failed to send webhook:", e, r.text)
        return False

if __name__ == "__main__":
    state = load_state()
    try:
        latest = fetch_latest()
    except Exception as e:
        print("Fetch error:", e)
        latest = None

    if latest:
        if latest["id"] != state.get("last"):
            sent = send_discord(latest)
            if sent:
                state["last"] = latest["id"]
                save_state(state)
                print("Sent and updated state:", latest["title"])
            else:
                print("Not sent — will retry next run.")
        else:
            print("No new updates.")
    else:
        print("Could not find latest item.")
