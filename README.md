# Müzik Botu — v1 (Faz 0 + Faz 1)

Bu ilk sürüm: mırıldanma / tek sesli (monofonik) enstrüman kaydını MIDI dosyasına çeviren
Telegram botu. Mimari, sonraki fazların (akor tespiti, solfej oyunları, egzersizler vb.)
birer modül olarak eklenebilmesi için `core/` (paylaşılan altyapı) ve `modules/`
(her faz kendi dosyasında) şeklinde ayrıldı.

## Gerekli API Anahtarları

Aşağıdaki isimleri Render'da **Environment** sekmesinden ekleyeceksin. Değer olarak
her servisten aldığın gerçek anahtarı yapıştıracaksın.

| Render'da eklenecek isim | Servis | Nereden alınır | Ne için |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram BotFather | https://t.me/BotFather (Telegram içinde `/newbot` yaz) | Botun kimliği, zorunlu |
| `SUPABASE_URL` | Supabase | Proje → Connect butonu (ya da Settings → Data API) | Veritabanı/hafıza adresi, zorunlu |
| `SUPABASE_SECRET_KEY` | Supabase | Proje → Settings → API Keys → "Secret keys" bölümü | Veritabanı erişim anahtarı, zorunlu. **Publishable key'i değil, Secret key'i kullan** — bot sunucu tarafında çalışıyor. `SUPABASE_JWKS_URL`'e ihtiyacımız yok, o kullanıcı girişi (auth) senaryoları için |
| `GROQ_API_KEY` | Groq | https://console.groq.com | Ücretsiz hızlı LLM — ileride koçluk/açıklama metinleri için, v1'de henüz kullanılmıyor ama şimdiden eklenebilir |

Yedek/opsiyonel (Gemini yerine, o sık sorun çıkardığı için önerilmiyor):

| Render'da eklenecek isim | Servis | Nereden alınır | Ne için |
|---|---|---|---|
| `CEREBRAS_API_KEY` | Cerebras | https://cloud.cerebras.ai | Groq'a ücretsiz alternatif |
| `OPENROUTER_API_KEY` | OpenRouter | https://openrouter.ai | Birden fazla modele tek anahtarla erişim, Groq/Cerebras çökerse yedek |

Faz 11 (Türk çalgıları) için ileride işe yarayabilir, v1'de gerekli değil:

| Render'da eklenecek isim | Servis | Nereden alınır | Ne için |
|---|---|---|---|
| `FREESOUND_API_KEY` | Freesound.org | https://freesound.org/apiv2/apply | Creative Commons ses örneği arama (tulum/zurna/kemençe kaydı) |

**API anahtarı gerektirmeyenler:** Render'ın kendisi, GitHub bağlantısı (Render arayüzünden bağlanır), ffmpeg/librosa/pretty_midi gibi tüm ses işleme kütüphaneleri (yerelde/serverde çalışır, dış servise bağlı değil).

## Render'a Deploy Adımları

1. Bu klasörü bir GitHub reposuna yükle (push et).
2. Render'da **New → Web Service** (veya Background Worker) seç, GitHub reponu bağla.
3. Render "Dockerfile bulundu" diyecek, environment olarak Docker'ı seçmesine izin ver.
4. **Environment** sekmesinden yukarıdaki tablodaki isimleri ekle (en azından `TELEGRAM_BOT_TOKEN` zorunlu; Supabase henüz bu v1'de kullanılmıyor ama ileride gerekecek, şimdiden ekleyebilirsin).
5. Deploy'u başlat. Loglarda "Bot başlatılıyor (polling modu)..." yazısını görürsen bot çalışıyor demektir.
6. Telegram'da botuna `/start` yaz, "🎤 Mırıldan / Çal → MIDI" butonuna bas, bir sesli mesaj gönder.

## Şu Anki Sınırlar (v1)

- Sadece tek sesli (monofonik) kayıtlar — mırıldanma, tek nota çalan enstrüman hattı
- Notalar en yakın batı yarım tonuna (12-TET) yuvarlanıyor
- Akorlu/polifonik enstrüman kayıtları (Basic Pitch ile), koma sesleri (mikrotonal), ayarlanabilir quantize sıkılığı ve diğer tüm fazlar roadmap'teki sırayla eklenecek
