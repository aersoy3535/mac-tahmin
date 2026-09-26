"""
Basit istatistiksel maç tahmin motoru.

Yöntem: Poisson dağılımı tabanlı "beklenen gol" (expected goals) modeli.
Bu, bahis şirketlerinin de temel aldığı klasik ve yaygın kabul görmüş bir
yöntemdir; makine öğrenmesi değildir ama takımların gol atma/yeme
eğilimlerini ve formunu birleştirerek olasılıksal bir tahmin üretir.

UYARI: Bu program hiçbir sonucu %100 garanti etmez. Futbol doğası gereği
öngörülemez bir spordur; bu sadece istatistiksel bir olasılık tahminidir.
"""
import math
from dataclasses import dataclass
from stats import TeamStats

MAX_GOALS = 6  # olasılık matrisinde denenecek maksimum gol sayısı (0..6)


def _poisson_pmf(k: int, lam: float) -> float:
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def _form_multiplier(team: TeamStats) -> float:
    """
    Form puanını (son N maç) 0.85 - 1.15 arasında bir çarpana çevirir.
    Ortalama form (maksimumun %50'si) -> çarpan 1.0.
    Çok iyi form -> hafif yukarı, çok kötü form -> hafif aşağı.
    Etki kasıtlı olarak sınırlı tutulmuştur (form tek başına maçı belirlemez).
    """
    if team.form_max_points == 0:
        return 1.0
    ratio = team.form_points / team.form_max_points  # 0..1
    return 0.85 + ratio * 0.30  # 0 -> 0.85, 1.0 -> 1.15


@dataclass
class MatchPrediction:
    home_team: str
    away_team: str
    home_expected_goals: float
    away_expected_goals: float
    home_win_pct: float
    draw_pct: float
    away_win_pct: float
    most_likely_score: str
    most_likely_score_pct: float
    top_scorelines: list  # [(skor_str, olasılık), ...] en olası 5 skor


def predict_match(home: TeamStats, away: TeamStats) -> MatchPrediction:
    # Ev/deplasman ortalaması yoksa genel ortalamayı kullan
    home_attack = home.avg_scored_home if home.avg_scored_home is not None else home.avg_scored
    away_defense = away.avg_conceded_away if away.avg_conceded_away is not None else away.avg_conceded
    away_attack = away.avg_scored_away if away.avg_scored_away is not None else away.avg_scored
    home_defense = home.avg_conceded_home if home.avg_conceded_home is not None else home.avg_conceded

    # Beklenen gol = (kendi hücum ort. + rakibin savunma zaafı ort.) / 2
    home_xg = (home_attack + away_defense) / 2
    away_xg = (away_attack + home_defense) / 2

    # Form çarpanı ile hafifçe ayarla
    home_xg *= _form_multiplier(home)
    away_xg *= _form_multiplier(away)

    # Ev sahibi avantajı (klasik ~%10 ek gol beklentisi)
    home_xg *= 1.10

    home_xg = max(home_xg, 0.05)
    away_xg = max(away_xg, 0.05)

    # Skor olasılık matrisi
    score_probs = {}
    for h in range(MAX_GOALS + 1):
        for a in range(MAX_GOALS + 1):
            score_probs[(h, a)] = _poisson_pmf(h, home_xg) * _poisson_pmf(a, away_xg)

    home_win = sum(p for (h, a), p in score_probs.items() if h > a)
    draw = sum(p for (h, a), p in score_probs.items() if h == a)
    away_win = sum(p for (h, a), p in score_probs.items() if h < a)

    # Normalize (matris kesildiği için toplam tam 1 olmayabilir)
    total = home_win + draw + away_win
    home_win, draw, away_win = home_win / total, draw / total, away_win / total

    sorted_scores = sorted(score_probs.items(), key=lambda kv: kv[1], reverse=True)
    top5 = [(f"{h}-{a}", round(p / total * 100, 1)) for (h, a), p in sorted_scores[:5]]
    best_score, best_pct = top5[0]

    return MatchPrediction(
        home_team=home.team_name,
        away_team=away.team_name,
        home_expected_goals=round(home_xg, 2),
        away_expected_goals=round(away_xg, 2),
        home_win_pct=round(home_win * 100, 1),
        draw_pct=round(draw * 100, 1),
        away_win_pct=round(away_win * 100, 1),
        most_likely_score=best_score,
        most_likely_score_pct=best_pct,
        top_scorelines=top5,
    )
