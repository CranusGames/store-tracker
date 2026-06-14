"""
Daily ranking fetcher — run by GitHub Actions (or manually).
Reads previous data/*.json for rise/fall comparison,
then overwrites with fresh data + change indicators.
"""

import json
from datetime import date
from pathlib import Path

import scrapers.apple as apple
import scrapers.google_play as gplay

DATA  = Path("data")
DATA.mkdir(exist_ok=True)
TODAY = str(date.today())

SECTIONS = [
    ("appstore",  "apps",  "tr", lambda: apple.fetch_top_apps("tr")),
    ("appstore",  "apps",  "us", lambda: apple.fetch_top_apps("us")),
    ("appstore",  "games", "tr", lambda: apple.fetch_top_games("tr")),
    ("appstore",  "games", "us", lambda: apple.fetch_top_games("us")),
    ("playstore", "apps",  "tr", lambda: gplay.fetch_top_apps("tr")),
    ("playstore", "apps",  "us", lambda: gplay.fetch_top_apps("us")),
    ("playstore", "games", "tr", lambda: gplay.fetch_top_games("tr")),
    ("playstore", "games", "us", lambda: gplay.fetch_top_games("us")),
]


def _load_prev(key: str) -> dict:
    p = DATA / f"{key}.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return {r["app_id"]: r["rank"] for r in d.get("rankings", [])}
        except Exception:
            pass
    return {}


def _change(rank: int, prev_rank):
    if prev_rank is None:
        return "new", 0
    diff = prev_rank - rank
    if diff > 0:
        return f"+{diff}", diff
    if diff < 0:
        return str(diff), diff
    return "=", 0


def _save(key: str, apps: list, prev: dict):
    rankings = []
    for i, a in enumerate(apps):
        rank = i + 1
        ch, chv = _change(rank, prev.get(a["app_id"]))
        rankings.append({
            "rank":         rank,
            "app_id":       a.get("app_id", ""),
            "app_name":     a.get("app_name", ""),
            "developer":    a.get("developer", ""),
            "icon_url":     a.get("icon_url", ""),
            "installs":     a.get("installs", ""),
            "rating":       a.get("rating", 0),
            "rating_count": a.get("rating_count", 0),
            "change":       ch,
            "change_val":   chv,
        })
    out = {"date": TODAY, "rankings": rankings}
    (DATA / f"{key}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  ✓ {key}: {len(rankings)} apps")


if __name__ == "__main__":
    print(f"Fetching rankings — {TODAY}")
    for platform, category, country, fetcher in SECTIONS:
        key = f"{platform}-{category}-{country}"
        print(f"  {key}…")
        prev = _load_prev(key)
        apps = fetcher()
        _save(key, apps, prev)

    (DATA / "meta.json").write_text(
        json.dumps({"last_fetch": TODAY}, ensure_ascii=False), encoding="utf-8"
    )
    print("Done.")
