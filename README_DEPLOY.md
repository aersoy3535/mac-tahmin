# Web Uygulamasını Ücretsiz Olarak İnternete Koyma (Render.com)

Bu, dayının telefonundan bir linke tıklayıp tüm liglerin maç tahminlerini
görebileceği canlı bir web sitesi kurmanın adımlarıdır. Kod yazmana veya
komut satırı (terminal) kullanmana gerek yok — hepsi tarayıcıdan, tıklayarak
yapılıyor.

**Toplam süre: ~15 dakika.**

---

## 1. Adım — GitHub hesabı aç (yoksa)

GitHub, kodunu saklayacağımız yer. Render, oradan kodunu okuyup siteyi kuruyor.

1. https://github.com adresine git
2. Ücretsiz hesap oluştur (e-posta ile)

## 2. Adım — Yeni bir "repository" (depo) oluştur

1. Sağ üstteki **"+"** işaretine tıkla → **"New repository"**
2. Repository name: `mac-tahmin` (istediğin ismi verebilirsin)
3. **Public** (herkese açık) seçili kalsın — Render'ın ücretsiz planı bunu istiyor
4. **"Create repository"** butonuna tıkla

## 3. Adım — Dosyaları GitHub'a yükle

1. Az önce açılan depo sayfasında **"uploading an existing file"** linkine tıkla
2. Bu `webapp` klasöründeki **tüm dosyaları** (alt klasör olan `templates`
   dahil) sürükleyip bırak:
   - `app.py`
   - `aggregator.py`
   - `api_client.py`
   - `cache.py`
   - `stats.py`
   - `predictor.py`
   - `requirements.txt`
   - `Procfile`
   - `.gitignore`
   - `templates/index.html`
3. Alt kısımda commit mesajı olarak "İlk yükleme" gibi bir şey yaz
4. **"Commit changes"** butonuna tıkla

> Not: `templates` klasörünü tek tek dosya olarak sürüklersen GitHub otomatik
> olarak `templates/index.html` yolunu koruyacaktır — dosya adının başına
> `templates/` yazman gerekmez, klasör yapısını GitHub kendisi algılar
> (Dosyaları klasör olarak sürükleyip bırakman yeterli).

## 4. Adım — Render.com hesabı aç

1. https://render.com adresine git → **"Get Started for Free"**
2. **"Sign up with GitHub"** ile giriş yap (en kolayı bu — hesapları otomatik bağlar)

## 5. Adım — Yeni Web Service oluştur

1. Render panelinde **"New +"** → **"Web Service"**
2. Az önce oluşturduğun `mac-tahmin` deposunu seç ve **"Connect"**
3. Ayarlar ekranında:
   - **Name:** `mac-tahmin` (bu, sitenin adresine yansıyacak: `mac-tahmin.onrender.com`)
   - **Region:** Frankfurt (Türkiye'ye en yakın seçenek)
   - **Runtime:** Python 3 (otomatik algılanmalı)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** **Free**

## 6. Adım — API anahtarını gizli ayar olarak ekle

Aynı ekranda aşağı in, **"Advanced"** → **"Add Environment Variable"**:

- **Key:** `FOOTBALL_DATA_API_KEY`
- **Value:** football-data.org'dan aldığın ücretsiz API anahtarı
  (yoksa: https://www.football-data.org/client/register — e-posta ile
  saniyeler içinde alınıyor)

## 7. Adım — Yayınla

**"Create Web Service"** butonuna tıkla. Render otomatik olarak kodu çekip
kuracak (~2-5 dakika sürer, ekranda log akışını izleyebilirsin).

Kurulum bitince sayfanın üstünde bir link göreceksin, örn:
`https://mac-tahmin.onrender.com`

Bu linki dayına gönder — telefondan açtığında tüm liglerin tahminlerini görecek!

---

## Bilmen gerekenler

- **İlk açılış yavaş olabilir:** Ücretsiz planda site 15 dakika kullanılmayınca
  "uyuyor"; biri linke tıkladığında ~30-60 saniye içinde uyanıyor. Sonraki
  tıklamalar hızlı. Bu ücretsiz planın doğal bir özelliği, bir hata değil.
- **İlk sayfa yüklemesi 2-3 dakika sürebilir:** Uygulama ilk açıldığında (veya
  "Şimdi Yenile" butonuna basıldığında) 12 lig için veri çekip hesaplama
  yapıyor; football-data.org'un ücretsiz planı dakikada 10 istekle sınırlı
  olduğu için bu biraz zaman alıyor. Sonuçlar 3 saat boyunca önbellekte
  tutuluyor, o süre içindeki ziyaretler anında açılıyor.
- **Kodda değişiklik yapmak istersen:** GitHub'daki dosyayı düzenleyip
  "Commit" dersen, Render otomatik olarak siteyi yeniden yayınlar (birkaç
  dakika sürer).
- **Sorun çıkarsa:** Render panelindeki **"Logs"** sekmesinden ne hata
  aldığını görebilirsin. En sık karşılaşılan sorun: `FOOTBALL_DATA_API_KEY`
  ortam değişkeninin yanlış girilmiş olması.
