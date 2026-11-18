#!/usr/bin/env python3
"""
CROUS watcher: checks trouverunlogement.lescrous.fr search pages and sends
a Telegram message as soon as a new accommodation appears.

Config via environment variables (set them as GitHub Secrets / Variables):
  TELEGRAM_TOKEN    - bot token from @BotFather
  TELEGRAM_CHAT_ID  - your chat id (see README)
  CROUS_URLS        - one or more search URLs, separated by spaces or newlines
                      (copy them from your browser after searching on the site)
  CROUS_KEYWORDS    - optional: residence names to keep, separated by ";"
                      e.g. "Jean Zay; Cité U; Antony". Empty = notify everything.
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup

BASE = "https://trouverunlogement.lescrous.fr"
STATE_FILE = Path(__file__).with_name("seen.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}
ACC_RE = re.compile(r"/tools/\d+/accommodations/(\d+)")
MAX_PAGES = 15


def with_page(url: str, page: int) -> str:
    p = urlparse(url)
    q = parse_qs(p.query)
    q["page"] = [str(page)]
    return urlunparse(p._replace(query=urlencode(q, doseq=True)))


def card_of(a):
    """Walk up from the link to the enclosing card element."""
    node = a
    for _ in range(8):
        node = node.parent
        if node is None:
            return a
        if "fr-card" in node.get("class", []) or node.name in ("li", "article"):
            return node
    return a


def parse(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for a in soup.find_all("a", href=ACC_RE):
        acc_id = ACC_RE.search(a["href"]).group(1)
        if acc_id in found:
            continue
        card = card_of(a)
        text = " ".join(card.get_text(" ", strip=True).split())
        title = " ".join(a.get_text(" ", strip=True).split()) or text[:80]
        found[acc_id] = {
            "title": title,
            "details": text[:300],
            "url": urljoin(BASE, a["href"]),
        }
    return found


def fetch_all(search_url: str) -> dict:
    results = {}
    for page in range(1, MAX_PAGES + 1):
        r = requests.get(with_page(search_url, page), headers=HEADERS, timeout=30)
        r.raise_for_status()
        batch = parse(r.text)
        new = {k: v for k, v in batch.items() if k not in results}
        if not new:
            break
        results.update(new)
        time.sleep(1)
    return results


def keep(item: dict, keywords: list) -> bool:
    if not keywords:
        return True
    hay = (item["title"] + " " + item["details"]).lower()
    return any(k in hay for k in keywords)


def send_telegram(token: str, chat_id: str, text: str):
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"},
        timeout=30,
    )
    r.raise_for_status()


def main():
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    urls = os.environ.get("CROUS_URLS", "").split()
    keywords = [k.strip().lower() for k in os.environ.get("CROUS_KEYWORDS", "").split(";") if k.strip()]
    if not (token and chat_id and urls):
        sys.exit("Missing TELEGRAM_TOKEN, TELEGRAM_CHAT_ID or CROUS_URLS")

    if "--test" in sys.argv:
        send_telegram(token, chat_id, "✅ CROUS watcher: тестовое сообщение, всё работает.")
        print("test message sent")
        return

    current = {}
    for url in urls:
        for k, v in fetch_all(url).items():
            if keep(v, keywords):
                current[k] = v
    print(f"{len(current)} matching offer(s) online")

    prev = set(json.loads(STATE_FILE.read_text())) if STATE_FILE.exists() else set()
    new_ids = [k for k in current if k not in prev]

    for k in new_ids:
        it = current[k]
        send_telegram(token, chat_id,
                      f"🏠 Новое предложение CROUS!\n\n{it['title']}\n{it['details']}\n\n👉 {it['url']}")
        print("notified", k, it["title"])

    # Store only what is online now, so an offer that disappears and comes back is notified again.
    STATE_FILE.write_text(json.dumps(sorted(current), indent=0))


if __name__ == "__main__":
    main()
