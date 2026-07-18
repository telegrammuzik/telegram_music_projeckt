"""
Tüm ortam değişkenlerinin (API anahtarları vb.) tek okunduğu yer.
Yeni bir faz/modül eklendiğinde, o modülün ihtiyaç duyduğu değişkeni buraya ekle,
kodun başka hiçbir yerinde doğrudan os.environ okuma.
"""

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Supabase'in "Connect" ekranından kopyaladığın isimle birebir aynı: SUPABASE_SECRET_KEY
# (SUPABASE_PUBLISHABLE_KEY ve SUPABASE_JWKS_URL bu bot için kullanılmıyor —
# onlar tarayıcı tarafı / kullanıcı girişi (auth) senaryoları için, bizim
# server-side veri okuma/yazma işimizde secret key yeterli)
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Şu an hiçbir modül bunları kullanmıyor (v1 sadece Faz 1), ama anahtarlar
# zaten alındığı için burada tanımlı — ileride LLM/örnek ses modülleri
# eklendiğinde doğrudan buradan okunacak.
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
FREESOUND_API_KEY = os.environ.get("FREESOUND_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN ortam değişkeni bulunamadı. "
        "Render'da Environment sekmesinden ekle (bkz. README.md)."
    )
