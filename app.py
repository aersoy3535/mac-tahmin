"""
Maç Tahmin Web Uygulaması.

Sayfa açıldığında önbellekteki (veya gerekirse tazelenmiş) tahminleri
liglere göre gruplanmış şekilde gösterir. "Şimdi Yenile" butonu önbelleği
zorla tazeler (bu ~2-3 dakika sürebilir, çünkü 12 lig taranıyor).
"""
import time

from flask import Flask, redirect, render_template, url_for

import cache

app = Flask(__name__)


@app.route("/")
def index():
    data = cache.get_or_refresh()
    age_minutes = int((time.time() - data["generated_at"]) / 60)
    total_matches = sum(len(v) for v in data["leagues"].values())
    return render_template(
        "index.html",
        leagues=data["leagues"],
        age_minutes=age_minutes,
        total_matches=total_matches,
    )


@app.route("/yenile", methods=["POST"])
def refresh_now():
    cache.get_or_refresh(force=True)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
