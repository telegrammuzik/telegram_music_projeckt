"""
Müzik Botu — v1 (Faz 0 iskeleti + Faz 1: mırıldanma/monofonik çalış -> MIDI)

Yeni bir faz eklerken:
1. modules/ altına yeni bir dosya ekle (hum_to_midi.py gibi)
2. Ana menüye bir buton ekle (MAIN_MENU)
3. menu_callback içinde o butonun callback_data'sına bir dal ekle
Mevcut fazlara dokunmadan böyle genişletilir.
"""

import logging
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from core.config import TELEGRAM_BOT_TOKEN


class _HealthHandler(BaseHTTPRequestHandler):
    """Render'ın 'servis ayakta mı' kontrolü ve UptimeRobot ping'i için basit
    bir HTTP cevabı. Bot kendisi Telegram'a 'polling' ile bağlanıyor, ayrı bir
    web sunucusuna ihtiyacı yok — ama Render'ın port bekleyen sağlık kontrolü
    ve uyanık tutma servisi (UptimeRobot vb.) bu adrese HTTP isteği atacak."""

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - bot calisiyor")

    def do_HEAD(self):
        # Bazı ping servisleri (UptimeRobot dahil) GET yerine HEAD isteği
        # gönderebilir — bu tanımlı olmazsa varsayılan olarak 501 dönüp
        # servis "down" gibi görünür.
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Render loglarını gereksiz istek kayitlariyla kirletmesin


def _start_health_server():
    port = int(os.environ.get("PORT", 10000))
    # ThreadingHTTPServer: her istek ayrı bir thread'de karşılanır, ağır ses
    # işleme sırasında ping isteği kuyrukta bekleyip zaman aşımına uğramasın.
    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    server.serve_forever()
from core.audio import convert_to_wav
from modules.hum_to_midi import transcribe_to_midi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎤 Mırıldan / Çal → MIDI", callback_data="menu:hum_to_midi")],
    # Diğer fazlar (akor tespiti, egzersizler, solfej, vb.) buraya buton olarak eklenecek
])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "Merhaba! Müzik botuna hoş geldin. Ne yapmak istersin?",
        reply_markup=MAIN_MENU,
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu:hum_to_midi":
        context.user_data["mode"] = "hum_to_midi"
        await query.edit_message_text(
            "Şarkıyı mırıldan ya da tek sesli çal, sesli mesaj (veya ses dosyası) "
            "olarak gönder. Sana MIDI dosyası olarak geri döneceğim.\n\n"
            "Not: bu ilk sürüm tek sesli (monofonik) kayıtlar için — akorlu çalışlar "
            "yakında ayrı bir modülle eklenecek."
        )


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if mode != "hum_to_midi":
        await update.message.reply_text(
            "Önce menüden '🎤 Mırıldan / Çal → MIDI' butonuna basmalısın.",
            reply_markup=MAIN_MENU,
        )
        return

    voice = update.message.voice or update.message.audio
    if voice is None:
        await update.message.reply_text("Bir ses dosyası veya sesli mesaj göndermelisin.")
        return

    await update.message.reply_text("Alındı, işleniyor... 🎧")

    tg_file = await context.bot.get_file(voice.file_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "girdi_ses")
        await tg_file.download_to_drive(input_path)

        try:
            wav_path = convert_to_wav(input_path)
            midi_path = os.path.join(tmpdir, "cikti.mid")
            _, note_count = transcribe_to_midi(wav_path, midi_path)

            if note_count == 0:
                await update.message.reply_text(
                    "Kayıtta net bir nota algılayamadım. Daha net ve tek sesli "
                    "mırıldanıp tekrar dener misin?"
                )
                return

            with open(midi_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename="melodi.mid",
                    caption=f"{note_count} nota tespit edildi. DAW'ına sürükleyip kullanabilirsin.",
                )
        except Exception as e:
            logger.exception("Ses işleme hatası")
            await update.message.reply_text(
                f"Bir hata oluştu, tekrar dener misin? (Detay: {e})"
            )


def main():
    # Render'ın "servis ayakta mı" kontrolü ve UptimeRobot ping'i için ayrı bir
    # thread'de basit bir HTTP sunucusu başlat (bot Telegram'a polling ile
    # bağlanıyor, kendi başına bir web portu açmıyor).
    threading.Thread(target=_start_health_server, daemon=True).start()
    logger.info("Sağlık kontrolü (health check) sunucusu başlatıldı.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))

    logger.info("Bot başlatılıyor (polling modu)...")
    app.run_polling()


if __name__ == "__main__":
    main()
