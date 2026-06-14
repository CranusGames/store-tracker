import requests

_BASE   = "https://itunes.apple.com/{country}/rss/topfreeapplications/limit=20/{suffix}json"
_LOOKUP = "https://itunes.apple.com/lookup"
_HDR    = {"User-Agent": "StoreTracker/1.0"}


def fetch_top_apps(country="us"):
    return _fetch(country, "")


def fetch_top_games(country="us"):
    return _fetch(country, "genre=6014/")


def _fetch(country, suffix):
    url = _BASE.format(country=country, suffix=suffix)
    try:
        r = requests.get(url, timeout=15, headers=_HDR)
        r.raise_for_status()
        entries = r.json().get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        apps = [
            {
                "app_id":   e.get("id", {}).get("attributes", {}).get("im:id", ""),
                "app_name": e.get("im:name", {}).get("label", ""),
                "developer": e.get("im:artist", {}).get("label", ""),
                "icon_url": (e.get("im:image") or [{}])[-1].get("label", ""),
            }
            for e in entries[:20]
        ]
        return _enrich(apps, country)
    except Exception as ex:
        print(f"[Apple] {country} suffix={suffix!r} error: {ex}")
        return []


def _enrich(apps: list, country: str) -> list:
    if not apps:
        return apps
    ids = ",".join(a["app_id"] for a in apps if a.get("app_id"))
    try:
        r = requests.get(
            _LOOKUP,
            params={"id": ids, "country": country},
            timeout=15,
            headers=_HDR,
        )
        r.raise_for_status()
        data = {str(item["trackId"]): item for item in r.json().get("results", [])}
        for app in apps:
            info = data.get(app["app_id"], {})
            app["rating_count"] = info.get("userRatingCount", 0) or 0
            app["rating"]       = round(info.get("averageUserRating", 0) or 0, 1)
            app["installs"]     = ""
    except Exception as ex:
        print(f"[Apple] enrich {country}: {ex}")
        for app in apps:
            app.setdefault("rating_count", 0)
            app.setdefault("rating", 0)
            app.setdefault("installs", "")
    return apps
