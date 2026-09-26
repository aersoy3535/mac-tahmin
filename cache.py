"""
Tahmin sonuçlarını bir JSON dosyasında önbellekler.

Önemli tasarım kararı: HİÇBİR fonksiyon burada bir HTTP isteğini
bloklamaz. 12 ligi taramak (~2-3 dakika, API'nin dakikada 10 istek
sınırı yüzünden) her zaman ARKA PLANDA ayrı bir thread'de yapılır.
Böylece:
  - gunicorn'un worker zaman aşımına takılmaz
  - Render'ın kendi proxy zaman aşımına takılmaz
  - Kullanıcı sayfayı her açtığında dakikalarca beklemez

get_status() anında döner: ya önbellekteki (belki biraz eski) veriyi
verir ya da veri hiç yoksa None döner ve arka planda taramayı tetikler.
"""
import json
import os
import threading
import time

from aggregator import generate_all_predictions
from api_client import FootballDataClient

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")
TTL_SECONDS = 3 * 60 * 60  # 3 saat

_refresh_lock = threading.Lock()
_refresh_in_progress = False
_last_error = None


def _load_raw():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_raw(data: dict):
    # Geçici dosyaya yazıp atomik olarak yer değiştir: yazma sırasında
    # aynı anda okuyan bir istek yarım/bozuk dosya görmesin diye.
    tmp_path = CACHE_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp_path, CACHE_PATH)


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


def _do_refresh():
    """Arka plan thread'inde çalışır. Hiçbir HTTP isteğini bloklamaz."""
    global _refresh_in_progress, _last_error
    try:
        client = FootballDataClient()
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
        _last_error = None
    except Exception as e:  # API key eksik, rate limit, ağ hatası vs.
        _last_error = str(e)
    finally:
        with _refresh_lock:
            _refresh_in_progress = False


def trigger_background_refresh() -> bool:
    """Zaten devam eden bir tarama yoksa yeni bir tane başlatır. Bloklamaz."""
    global _refresh_in_progress
    with _refresh_lock:
        if _refresh_in_progress:
            return False
        _refresh_in_progress = True
    threading.Thread(target=_do_refresh, daemon=True).start()
    return True


def is_refreshing() -> bool:
    return _refresh_in_progress


def get_last_error():
    return _last_error


def get_status():
    """
    Anında döner (asla API'ye kendisi istek atmaz):
      (data, is_stale, is_refreshing)
    data None ise önbellek hiç yok demektir (ilk açılış).
    Veri eskiyse veya hiç yoksa arka plan taramasını tetikler.
    """
    data = _load_raw()
    stale = data is None or (time.time() - data.get("generated_at", 0)) > TTL_SECONDS
    if stale:
        trigger_background_refresh()
    return data, stale, is_refreshing()
