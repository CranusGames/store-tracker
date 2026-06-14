"""
Google Play scraper.

Apps  → embedded ds:4 cluster data from /store/apps/top (IP-based)
Games → google_play_scraper.search() (includes install counts)
"""

import re
import json
import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_AF_RE  = re.compile(r"AF_initDataCallback[\s\S]*?<\/script")
_KEY_RE = re.compile(r"(ds:.*?)'")
_VAL_RE = re.compile(r"data:([\s\S]*?), sideChannel: {}}\);<\/")


def fetch_top_apps(country="tr"):
    return _fetch_apps(country)


def fetch_top_games(country="tr"):
    return _fetch_games(country)


# ── Apps ──────────────────────────────────────────────────────────────────────

def _fetch_apps(country: str):
    try:
        r = requests.get(
            "https://play.google.com/store/apps/top",
            params={"hl": "en", "gl": country.upper()},
            headers=_HEADERS, timeout=20,
        )
        r.raise_for_status()
        ds4 = _parse_ds4(r.text)
        if not ds4:
            return []
        return _extract_cluster(ds4)
    except Exception as e:
        print(f"[GPlay Apps] {country}: {e}")
        return []


def _parse_ds4(html: str):
    for block in _AF_RE.findall(html):
        keys = _KEY_RE.findall(block)
        vals = _VAL_RE.findall(block)
        if keys and vals and keys[0] == "ds:4":
            try:
                return json.loads(vals[0])
            except Exception:
                pass
    return None


def _fmt_installs(n) -> str:
    if not n or not isinstance(n, (int, float)):
        return ""
    n = int(n)
    if n >= 1_000_000_000:
        return f"{n // 1_000_000_000}B+"
    if n >= 1_000_000:
        return f"{n // 1_000_000}M+"
    if n >= 1_000:
        return f"{n // 1_000}K+"
    return str(n)


def _extract_cluster(ds4, cluster_idx=0):
    try:
        entries = ds4[0][1][cluster_idx][21][0]
    except (IndexError, TypeError):
        return []
    results = []
    for entry in entries[:20]:
        try:
            app_id    = entry[0][0] if isinstance(entry[0], list) else str(entry[0])
            title     = entry[3]  if len(entry) > 3  and isinstance(entry[3],  str) else ""
            developer = entry[14] if len(entry) > 14 and isinstance(entry[14], str) else ""
            icon_data = entry[1]  if len(entry) > 1  and isinstance(entry[1],  list) else None
            icon_url  = ""
            if icon_data and len(icon_data) > 3 and isinstance(icon_data[3], list):
                icon_url = icon_data[3][2] if len(icon_data[3]) > 2 else ""

            # Try to extract install count (position varies; try common slots)
            installs = ""
            rating   = 0.0
            rating_count = 0
            try:
                raw_installs = entry[13] if len(entry) > 13 else None
                installs = _fmt_installs(raw_installs)
            except Exception:
                pass
            try:
                raw_rating = entry[4][1] if len(entry) > 4 and isinstance(entry[4], list) else None
                if isinstance(raw_rating, (int, float)):
                    rating = round(float(raw_rating), 1)
            except Exception:
                pass

            results.append({
                "app_id":       app_id or "",
                "app_name":     title,
                "developer":    developer,
                "icon_url":     icon_url or "",
                "installs":     installs,
                "rating":       rating,
                "rating_count": rating_count,
            })
        except Exception:
            continue
    return results


# ── Games ─────────────────────────────────────────────────────────────────────

def _fetch_games(country: str):
    try:
        from google_play_scraper import search
        results = search("top free games", n_hits=20, lang="en", country=country)

        out = []
        for a in results[:20]:
            min_inst  = a.get("minInstalls", 0) or 0
            inst_str  = a.get("installs", "") or ""
            if not inst_str and min_inst:
                inst_str = _fmt_installs(min_inst)
            out.append({
                "app_id":       a.get("appId", ""),
                "app_name":     a.get("title", ""),
                "developer":    a.get("developer", ""),
                "icon_url":     a.get("icon", ""),
                "installs":     inst_str,
                "rating":       round(a.get("score", 0) or 0, 1),
                "rating_count": a.get("ratings", 0) or 0,
            })
        return out
    except Exception as e:
        print(f"[GPlay Games] {country}: {e}")
        return []
