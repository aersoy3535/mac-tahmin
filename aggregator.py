"""
Tüm desteklenen liglerdeki yaklaşan maçları çekip, her biri için tahmin üretir.

Verimlilik notu: Her takımın istatistiğini ayrı ayrı API isteğiyle çekmek
yerine, turnuva başına TEK bir "bitmiş maçlar" isteği atılır; o turnuvadaki
tüm takımların formu/gol ortalaması bu tek listeden hesaplanır. Böylece
200 maçlık bir tarama için ~12 turnuva x 2 istek (bitmiş + yaklaşan) yeterli
olur (free plan: dakikada 10 istek).
"""
from stats import compute_team_stats
from predictor import predict_match

# football-data.org ücretsiz planda yer alan 12 turnuva
COMPETITIONS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "DED": "Eredivisie",
    "PPL": "Primeira Liga",
    "ELC": "Championship",
    "BSA": "Brezilya Serie A",
    "CL": "UEFA Şampiyonlar Ligi",
    "WC": "Dünya Kupası",
    "EC": "UEFA Avrupa Şampiyonası",
}

MAX_UPCOMING_PER_COMPETITION = 17  # ~200 maç hedefi / 12 lig
FORM_SAMPLE_SIZE = 8                # form/gol ortalaması için son kaç maça bakılacak
MIN_FINISHED_FOR_STATS = 3           # tahmin üretebilmek için gereken min. bitmiş maç


def _build_team_stats_map(finished_matches: list) -> dict:
    """Bir turnuvanın bitmiş maç listesinden {team_id: TeamStats} üretir."""
    by_team = {}
    for m in finished_matches:
        if m["score"]["fullTime"]["home"] is None:
            continue  # skor yoksa (ör. iptal maç) atla
        for side in ("homeTeam", "awayTeam"):
            tid = m[side]["id"]
            by_team.setdefault(tid, {"name": m[side]["name"], "matches": []})
            by_team[tid]["matches"].append(m)

    stats_map = {}
    for tid, info in by_team.items():
        sample = sorted(info["matches"], key=lambda mm: mm["utcDate"], reverse=True)
        sample = sample[:FORM_SAMPLE_SIZE]
        if len(sample) < MIN_FINISHED_FOR_STATS:
            continue
        stats_map[tid] = compute_team_stats(tid, info["name"], sample)
    return stats_map


def generate_all_predictions(client, log=print) -> dict:
    """
    {lig_adi: [ {home, away, date, prediction, note}, ... ] } döner.
    prediction None ise (yeterli veri yoksa) note açıklama içerir.
    """
    results = {}
    for code, display_name in COMPETITIONS.items():
        log(f"  {display_name} ({code}) taranıyor...")
        try:
            finished = client.get_competition_matches(code, status="FINISHED")
        except RuntimeError as e:
            log(f"    bitmiş maçlar alınamadı: {e}")
            finished = []
        try:
            scheduled = client.get_competition_matches(code, status="SCHEDULED")
        except RuntimeError as e:
            log(f"    yaklaşan maçlar alınamadı: {e}")
            scheduled = []

        if not scheduled:
            log("    yaklaşan maç yok, atlanıyor.")
            continue

        stats_map = _build_team_stats_map(finished) if finished else {}
        scheduled_sorted = sorted(scheduled, key=lambda mm: mm["utcDate"])
        scheduled_sorted = scheduled_sorted[:MAX_UPCOMING_PER_COMPETITION]

        league_matches = []
        for m in scheduled_sorted:
            home_id, away_id = m["homeTeam"]["id"], m["awayTeam"]["id"]
            entry = {
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "date": m["utcDate"],
                "prediction": None,
                "note": None,
            }
            if home_id in stats_map and away_id in stats_map:
                entry["prediction"] = predict_match(stats_map[home_id], stats_map[away_id])
            else:
                entry["note"] = "Yeterli geçmiş maç verisi yok (sezon başı olabilir)."
            league_matches.append(entry)

        if league_matches:
            results[display_name] = league_matches

    return results
