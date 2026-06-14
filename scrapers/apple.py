import requests

_BASE = "https://itunes.apple.com/{country}/rss/topfreeapplications/limit=20/{suffix}json"


def fetch_top_apps(country="us"):
    return _fetch(country, "")


def fetch_top_games(country="us"):
    return _fetch(country, "genre=6014/")  # genre 6014 = Games


def _fetch(country, suffix):
    url = _BASE.format(country=country, suffix=suffix)
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "StoreTracker/1.0"})
        r.raise_for_status()
        entries = r.json().get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        return [
            {
                "app_id": e.get("id", {}).get("attributes", {}).get("im:id", ""),
                "app_name": e.get("im:name", {}).get("label", ""),
                "developer": e.get("im:artist", {}).get("label", ""),
                "icon_url": (e.get("im:image") or [{}])[-1].get("label", ""),
            }
            for e in entries[:20]
        ]
    except Exception as ex:
        print(f"[Apple] {country} suffix={suffix!r} error: {ex}")
        return []
