from datetime import date
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sys, os

# Ensure imports work regardless of working directory
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import database
import scrapers.apple as apple
import scrapers.google_play as gplay
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(title="Store Tracker")


# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch_all():
    today = str(date.today())
    print(f"[{today}] Fetching all rankings…")
    for country in ("tr", "us"):
        database.save_rankings("appstore",  "apps",  country, apple.fetch_top_apps(country))
        database.save_rankings("appstore",  "games", country, apple.fetch_top_games(country))
        database.save_rankings("playstore", "apps",  country, gplay.fetch_top_apps(country))
        database.save_rankings("playstore", "games", country, gplay.fetch_top_games(country))
    print("Done.")


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    database.init_db()
    if not database.get_rankings("appstore", "apps", "us"):
        fetch_all()
    scheduler = BackgroundScheduler(timezone="Europe/Istanbul")
    scheduler.add_job(fetch_all, "cron", hour=6, minute=0)
    scheduler.start()


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/rankings/{platform}/{category}/{country}")
def get_rankings(platform: str, category: str, country: str):
    today   = database.get_rankings(platform, category, country)
    prev    = database.get_prev_rankings(platform, category, country)
    prev_map = {r["app_id"]: r["rank"] for r in prev}

    enriched = []
    for entry in today:
        aid = entry["app_id"]
        prev_rank = prev_map.get(aid)
        if prev_rank is None:
            change = "new"
            change_val = 0
        else:
            change_val = prev_rank - entry["rank"]
            change = f"+{change_val}" if change_val > 0 else ("=" if change_val == 0 else str(change_val))
        enriched.append({**entry, "change": change, "change_val": change_val})

    return enriched


@app.get("/api/status")
def status():
    last = database.last_fetch_date("appstore", "apps", "us")
    return {"last_fetch": last, "today": str(date.today())}


@app.post("/api/refresh")
def refresh():
    fetch_all()
    return {"status": "ok", "date": str(date.today())}


# ── Frontend ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return (ROOT / "static" / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
