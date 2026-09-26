"""
Tahmin sonuçlarını bir JSON dosyasında önbellekler.

Neden gerekli: 12 lig için tahmin üretmek ~24 API isteği gerektiriyor ve
free plan dakikada 10 istekle sınırlı olduğundan tam bir tarama ~2-3 dakika
sürüyor. Her sayfa ziyaretinde bunu tekrar yapmak hem yavaş hem gereksiz
(fikstürler ve form birkaç saatte bir değişir). Bu yüzden sonuçlar
TTL_SECONDS süresince diskte saklanır; süre dolunca bir sonraki ziyarette
otomatik yenilenir.
"""
import json
import os
import time

from aggregator import generate_all_predictions
from api_client import FootballDataClient

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")
TTL_SECONDS = 3 * 60 * 60  # 3 saat


def _load_raw():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_raw(data: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _serialize_prediction(p):
    if p is None:
        return None
    return {
        "home_expected_goals": p.home_expected_goals,
        "away_expected_goals": p.away_expected_goals,
        "home_win_pct": p.home_win_pct,
        "draw_pct": p.draw_pct,
        "away_win_pct": p.away_win_pct,
        "most_likely_score": p.most_likely_score,
        "most_likely_score_pct": p.most_likely_score_pct,
    }


def refresh(client=None) -> dict:
    client = client or FootballDataClient()
    raw = generate_all_predictions(client)

    serializable = {}
    for league, matches in raw.items():
        serializable[league] = [
            {
                "home": m["home"],
                "away": m["away"],
                "date": m["date"],
                "prediction": _serialize_prediction(m["prediction"]),
                "note": m["note"],
            }
            for m in matches
        ]

    payload = {"generated_at": time.time(), "leagues": serializable}
    _save_raw(payload)
    return payload


def get_or_refresh(force: bool = False) -> dict:
    data = _load_raw()
    is_stale = data is None or (time.time() - data.get("generated_at", 0)) > TTL_SECONDS
    if force or is_stale:
        data = refresh()
    return data
