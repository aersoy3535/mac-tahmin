"""
Maç Tahmin Web Uygulaması.

Sayfa hiçbir zaman dakikalarca beklemez: veri hazırsa gösterir, değilse
(veya eskiyse) arka planda taramayı tetikler ve "hazırlanıyor" sayfası
gösterir (bu sayfa kendini birkaç saniyede bir otomatik yeniler).
"""
import time

from flask import Flask, redirect, render_template, url_for

import cache

app = Flask(__name__)


@app.route("/")
def index():
    data, stale, refreshing = cache.get_status()

    if data is None:
        return render_template("loading.html", error=cache.get_last_error())

    age_minutes = int((time.time() - data["generated_at"]) / 60)
    total_matches = sum(len(v) for v in data["leagues"].values())
    return render_template(
        "index.html",
        leagues=data["leagues"],
        age_minutes=age_minutes,
        total_matches=total_matches,
        refreshing=refreshing,
    )


@app.route("/yenile", methods=["POST"])
def refresh_now():
    cache.trigger_background_refresh()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
