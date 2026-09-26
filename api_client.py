"""
football-data.org API istemcisi.
Ücretsiz plan: 10 istek/dakika, 12 turnuva (PL, PD, BL1, SA, FL1, DED, PPL,
ELC, BSA, CL, WC, EC). API key: https://www.football-data.org/client/register
"""
import os
import time
import requests

BASE_URL = "https://api.football-data.org/v4"


class FootballDataClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("FOOTBALL_DATA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API anahtarı bulunamadı. FOOTBALL_DATA_API_KEY ortam "
                "değişkenini ayarla ya da FootballDataClient(api_key=...) kullan.\n"
                "Ücretsiz key: https://www.football-data.org/client/register"
            )
        self.headers = {"X-Auth-Token": self.api_key}
        self._last_request_time = 0.0
        self._min_interval = 6.5  # 10 istek/dk sınırını aşmamak için (~9/dk)

    def _get(self, endpoint: str, params: dict = None) -> dict:
        # Basit rate-limit koruması
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=15)
        self._last_request_time = time.time()

        if resp.status_code == 429:
            raise RuntimeError(
                "API rate limit aşıldı (dakikada 10 istek). Biraz bekleyip tekrar dene."
            )
        if resp.status_code == 403:
            raise RuntimeError(
                "Bu turnuvaya/veriye erişim izniniz yok (ücretsiz planın kapsamı dışında)."
            )
        if resp.status_code == 404:
            raise RuntimeError("Kayıt bulunamadı (takım/turnuva/id hatalı olabilir).")
        resp.raise_for_status()
        return resp.json()

    def get_competition_teams(self, competition_code: str) -> list:
        """Bir turnuvadaki takımları döner. Örn: 'PL', 'CL', 'PD', 'BL1'..."""
        data = self._get(f"/competitions/{competition_code}/teams")
        return data.get("teams", [])

    def get_competition_matches(self, competition_code: str, status: str = None) -> list:
        """
        Bir turnuvadaki TÜM maçları tek istekte döner (status verilirse filtreler:
        'FINISHED' veya 'SCHEDULED'). Bunu takım başına ayrı istek atmak yerine
        kullanmak API kotasını (dakikada 10 istek) çok daha verimli kullanır:
        200 maçlık bir analiz için takım başına istek yerine turnuva başına
        1-2 istek yeterli olur.
        """
        params = {"status": status} if status else {}
        data = self._get(f"/competitions/{competition_code}/matches", params=params)
        return data.get("matches", [])

    def get_team_matches(self, team_id: int, limit: int = 10, status: str = "FINISHED") -> list:
        """Bir takımın son bitmiş maçlarını döner (en yeniden en eskiye sıralı)."""
        params = {"status": status, "limit": limit}
        data = self._get(f"/teams/{team_id}/matches", params=params)
        matches = data.get("matches", [])
        matches.sort(key=lambda m: m["utcDate"], reverse=True)
        return matches[:limit]

    def find_team_id(self, competition_code: str, team_name: str) -> dict:
        """Takım adını (kısmi eşleşme, büyük/küçük harf duyarsız) turnuva içinde arar."""
        teams = self.get_competition_teams(competition_code)
        name_lower = team_name.strip().lower()
        # Önce tam eşleşme dene
        for t in teams:
            if t["name"].lower() == name_lower or t.get("shortName", "").lower() == name_lower:
                return t
        # Sonra kısmi eşleşme
        matches = [t for t in teams if name_lower in t["name"].lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(t["name"] for t in matches)
            raise ValueError(f"Birden fazla eşleşme bulundu: {names}. Daha net bir isim gir.")
        raise ValueError(
            f"'{team_name}' takımı '{competition_code}' turnuvasında bulunamadı. "
            f"Mevcut takımlar: {', '.join(t['name'] for t in teams)}"
        )
