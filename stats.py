"""
Takım istatistiklerini (form, gol ortalamaları, ev/deplasman ayrımı) hesaplar.
"""
from dataclasses import dataclass


@dataclass
class TeamStats:
    team_id: int
    team_name: str
    matches_analyzed: int
    form_points: int          # son N maçtaki puan (G=3, B=1, M=0)
    form_max_points: int
    form_string: str          # örn: "G-G-B-M-G" (en yeniden en eskiye)
    avg_scored: float         # genel gol ortalaması (attığı)
    avg_conceded: float       # genel gol ortalaması (yediği)
    avg_scored_home: float    # sadece ev sahibiyken attığı ortalama
    avg_conceded_home: float
    avg_scored_away: float    # sadece deplasmandayken attığı ortalama
    avg_conceded_away: float


def _result_for_team(match: dict, team_id: int) -> str:
    """Bir maçtaki sonucu takım açısından döner: 'G', 'B' veya 'M'."""
    home_id = match["homeTeam"]["id"]
    winner = match["score"]["winner"]  # 'HOME_TEAM' | 'AWAY_TEAM' | 'DRAW'
    if winner == "DRAW":
        return "B"
    is_home = home_id == team_id
    if (winner == "HOME_TEAM" and is_home) or (winner == "AWAY_TEAM" and not is_home):
        return "G"
    return "M"


def compute_team_stats(team_id: int, team_name: str, matches: list) -> TeamStats:
    """
    matches: api_client.get_team_matches() çıktısı (en yeniden en eskiye sıralı,
    sadece FINISHED maçlar).
    """
    if not matches:
        raise ValueError(f"{team_name} için analiz edilecek bitmiş maç bulunamadı.")

    points_map = {"G": 3, "B": 1, "M": 0}
    form_chars = []
    form_points = 0

    total_scored, total_conceded = 0, 0
    home_scored, home_conceded, home_games = 0, 0, 0
    away_scored, away_conceded, away_games = 0, 0, 0

    for m in matches:
        result = _result_for_team(m, team_id)
        form_chars.append(result)
        form_points += points_map[result]

        home_id = m["homeTeam"]["id"]
        home_goals = m["score"]["fullTime"]["home"] or 0
        away_goals = m["score"]["fullTime"]["away"] or 0

        if home_id == team_id:
            total_scored += home_goals
            total_conceded += away_goals
            home_scored += home_goals
            home_conceded += away_goals
            home_games += 1
        else:
            total_scored += away_goals
            total_conceded += home_goals
            away_scored += away_goals
            away_conceded += home_goals
            away_games += 1

    n = len(matches)
    return TeamStats(
        team_id=team_id,
        team_name=team_name,
        matches_analyzed=n,
        form_points=form_points,
        form_max_points=n * 3,
        form_string="-".join(form_chars),
        avg_scored=round(total_scored / n, 2),
        avg_conceded=round(total_conceded / n, 2),
        avg_scored_home=round(home_scored / home_games, 2) if home_games else None,
        avg_conceded_home=round(home_conceded / home_games, 2) if home_games else None,
        avg_scored_away=round(away_scored / away_games, 2) if away_games else None,
        avg_conceded_away=round(away_conceded / away_games, 2) if away_games else None,
    )
