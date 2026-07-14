"""
Müzik Botu — main.py

Mimari (Faz 0): main.py sadece Telegram etkileşimini ve menü yönlendirmesini
yönetir; gerçek işi modules/ altındaki dosyalar yapar. Yeni bir faz eklerken:
1. modules/ altına yeni bir dosya ekle
2. Aşağıdaki MENUS sözlüğüne bir buton ekle
3. Buton bir dosya bekliyorsa WAIT_HANDLERS'a bir işlev ekle, yoksa
   IMMEDIATE_ACTIONS'a ekle
Mevcut fazlara dokunmadan böyle genişletilir.

DÜRÜSTLÜK NOTU (genel): Bu botun birçok modülü kural tabanlı/DSP yöntemleriyle
yazıldı çünkü bu geliştirme ortamında ağ erişimi yok — gerçek eğitilmiş
modeller (Basic Pitch, DDSP, madmom/BTC, Magenta) kurulamadı. İlgili
modüllerin docstring'lerinde bu sınırlar ayrıca belirtiliyor. Bazı çok
parametreli özellikler (ör. egzersiz üretici) şimdilik sabit varsayılanlarla
çalışıyor (sadece kök nota seçilebiliyor) — tam çok adımlı sihirbazlar
ileride eklenebilir.
"""

import logging
import os
import tempfile
import threading
import traceback
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
from core.audio import convert_to_wav

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sağlık kontrolü / ping sunucusu (Render + UptimeRobot için)
# ---------------------------------------------------------------------------

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - bot calisiyor")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def _start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    server.serve_forever()


# ---------------------------------------------------------------------------
# Menü tanımları
# ---------------------------------------------------------------------------

ROOT_NOTES = ["C", "D", "E", "F", "G", "A", "B"]


def _kb(rows):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=cb) for t, cb in row] for row in rows])


MAIN_MENU = _kb([
    [("🎤 Mırıldan/Çal → MIDI", "menu:faz1")],
    [("🎼 Melodi Devamı (AI)", "menu:faz2")],
    [("🎹 Akorlar", "menu:faz3")],
    [("🏋️ Egzersizler", "menu:faz4")],
    [("🎧 Solfej Oyunları", "menu:faz5")],
    [("📖 Nota Okuma", "menu:faz6")],
    [("📚 Armoni Eğitimi", "menu:faz7")],
    [("🥁 Stüdyo Altyapı", "menu:faz8")],
    [("🖥️ Logic Pro Eğitimi", "menu:faz9")],
    [("🎚️ Mix & Mastering", "menu:faz10")],
    [("🪕 Türk Çalgıları", "menu:faz11")],
    [("✍️ Beste Araçları", "menu:beste")],
    [("🧰 Diğer Araçlar", "menu:araclar")],
])

SUBMENUS = {
    "faz1": _kb([
        [("Mırıldanma / tek sesli çal", "wait:hum_to_midi")],
        [("Akorlu/çoklu nota çal (deneysel)", "wait:poly_to_midi")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz2": _kb([
        [("Bir MIDI gönder, devamını üreteyim", "wait:melody_continue")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz3": _kb([
        [("Sesten akor tespiti", "wait:chord_detect")],
        [("Melodiyi armonize et (MIDI gönder)", "wait:harmonize")],
        [("Ruh haline göre akor öner", "menu:faz3_mood")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz3_mood": _kb([
        [("Mutlu", "act:mood:mutlu"), ("Hüzünlü", "act:mood:hüzünlü")],
        [("Epik", "act:mood:epik"), ("Nostaljik", "act:mood:nostaljik")],
        [("Lo-fi", "act:mood:lofi"), ("Gerilim", "act:mood:gerilim")],
        [("⬅️ Geri", "menu:faz3")],
    ]),
    "faz4": _kb([
        [("Gam egzersizi", "menu:faz4_scale")],
        [("Arpej egzersizi", "menu:faz4_arp")],
        [("Riff üret", "menu:faz4_riff")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz4_scale": _kb([[(n, f"act:scale:{n}") for n in ROOT_NOTES], [("⬅️ Geri", "menu:faz4")]]),
    "faz4_arp": _kb([[(n, f"act:arp:{n}") for n in ROOT_NOTES], [("⬅️ Geri", "menu:faz4")]]),
    "faz4_riff": _kb([[(n, f"act:riff:{n}") for n in ROOT_NOTES], [("⬅️ Geri", "menu:faz4")]]),
    "faz5": _kb([
        [("Aralık tanıma oyunu", "act:game:interval")],
        [("Nota tanıma oyunu", "act:game:note")],
        [("Tını tanıma oyunu", "act:game:timbre")],
        [("Söylediğim notayı kontrol et", "wait:check_sung_note")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz6": _kb([
        [("Ders 1: Porte ve Anahtarlar", "act:lesson:note:0")],
        [("Ders 2: Sol Anahtarında Notalar", "act:lesson:note:1")],
        [("Ders 3: Ritim Değerleri", "act:lesson:note:2")],
        [("Quiz: Nota konumu", "act:quiz:note_pos")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz7": _kb([
        [("Ders: Akor Fonksiyonları", "act:lesson:harmony:0")],
        [("Ders: Kadanslar", "act:lesson:harmony:1")],
        [("Ders: Ses Yürüyüşü", "act:lesson:harmony:2")],
        [("Quiz: Akor fonksiyonu", "act:quiz:chord_func")],
        [("Doğu/Makam Armonisi (tanıtım)", "act:makam_intro")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz8": _kb([
        [("Pop davul", "act:drum:pop"), ("Rock davul", "act:drum:rock")],
        [("Trap davul", "act:drum:trap"), ("Akustik davul", "act:drum:akustik")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz9": _kb([
        [("Kayıt (Recording)", "act:logic:0")],
        [("MIDI Düzenleme", "act:logic:1")],
        [("Enstrümanlar/Pluginler", "act:logic:2")],
        [("Mixer", "act:logic:3")],
        [("Otomasyon", "act:logic:4")],
        [("Kısayollar/Workflow", "act:logic:5")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz10": _kb([
        [("Mix'imi analiz et", "wait:mix_analyze")],
        [("Referansla karşılaştır", "wait:mix_compare_1")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "faz11": _kb([
        [("Tulum", "act:turkish:tulum"), ("Zurna", "act:turkish:zurna")],
        [("Klasik Kemençe", "act:turkish:klasik_kemençe"), ("Kabak Kemane", "act:turkish:kabak_kemane")],
        [("Kaval", "act:turkish:kaval"), ("Ney", "act:turkish:ney")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "beste": _kb([
        [("İnversiyon", "wait:motif_invert"), ("Retrograd", "wait:motif_retrograde")],
        [("Sekans", "wait:motif_sequence"), ("Kontrpuan üret", "wait:motif_counter")],
        [("Modülasyon önerisi", "wait:motif_modulation")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "araclar": _kb([
        [("🎸 Akort aleti (tuner)", "wait:tuner")],
        [("🎙️ Vokal aralığı tespiti", "wait:vocal_range")],
        [("🎼 MIDI'den tab çıkar", "wait:tab_export")],
        [("🔤 Söz hece/kafiye sayacı", "wait:lyrics")],
        [("🎛️ Doğaçlama backing loop", "menu:araclar_backing")],
        [("🎚️ Minus-one (vokal azaltma)", "wait:minus_one")],
        [("📋 Kompozisyon şablonu", "act:template:basit_pop")],
        [("🎹 Akor diyagramı", "menu:araclar_chords")],
        [("🎙️ Kayıt kalitesi kontrolü", "wait:mic_check")],
        [("🧭 Bugün ne çalışmalıyım?", "act:coach")],
        [("🎲 Günlük mini meydan okuma", "act:daily_challenge")],
        [("⬅️ Ana menü", "menu:main")],
    ]),
    "araclar_chords": _kb([
        [("C", "act:chorddiag:C:maj"), ("G", "act:chorddiag:G:maj"), ("D", "act:chorddiag:D:maj")],
        [("A", "act:chorddiag:A:maj"), ("E", "act:chorddiag:E:maj"), ("F", "act:chorddiag:F:maj")],
        [("Am", "act:chorddiag:A:min"), ("Dm", "act:chorddiag:D:min"), ("Em", "act:chorddiag:E:min")],
        [("⬅️ Geri", "menu:araclar")],
    ]),
    "araclar_backing": _kb([
        [("Mutlu+Pop", "act:backing:mutlu:pop"), ("Hüzünlü+Akustik", "act:backing:hüzünlü:akustik")],
        [("Epik+Rock", "act:backing:epik:rock"), ("Lo-fi+Trap", "act:backing:lofi:trap")],
        [("⬅️ Geri", "menu:araclar")],
    ]),
}


def get_menu(key):
    if key == "main":
        return MAIN_MENU
    return SUBMENUS.get(key)


# ---------------------------------------------------------------------------
# "Bekleme modu" işleyicileri: kullanıcı bir dosya (ses/MIDI) gönderdiğinde
# hangi modülün hangi fonksiyonunu çağıracağını burada topluyoruz. Her işlev
# (girdi_dosya_yolu, context) alır, (cevap_metni, gönderilecek_dosya_yolu_veya_None) döner.
# ---------------------------------------------------------------------------

def _wait_hum_to_midi(path, context):
    from modules.hum_to_midi import transcribe_to_midi
    wav = convert_to_wav(path)
    out = tempfile.mktemp(suffix=".mid")
    _, n = transcribe_to_midi(wav, out)
    if n == 0:
        return "Net bir nota algılayamadım. Daha net ve tek sesli mırıldanıp tekrar dener misin?", None
    return f"{n} nota tespit edildi.", out


def _wait_poly_to_midi(path, context):
    from modules.instrument_polyphonic import transcribe_polyphonic
    wav = convert_to_wav(path)
    out = tempfile.mktemp(suffix=".mid")
    _, n = transcribe_polyphonic(wav, out)
    if n == 0:
        return "Net bir nota/akor algılayamadım.", None
    return f"{n} nota tespit edildi (deneysel polifonik mod).", out


def _wait_melody_continue(path, context):
    from modules.melody_continue import continue_melody
    out = tempfile.mktemp(suffix=".mid")
    _, orig, gen, key = continue_melody(path, out, num_notes=16)
    return f"Tespit edilen ton: {key}. {orig} orijinal nota + {gen} yeni nota üretildi.", out


def _wait_chord_detect(path, context):
    from modules.chords import detect_chords_from_audio
    wav = convert_to_wav(path)
    chords = detect_chords_from_audio(wav, detailed=False)
    if not chords:
        return "Net bir akor tespit edemedim.", None
    lines = [f"{label}  ({s:.1f}s-{e:.1f}s)" for label, s, e in chords]
    return "Tespit edilen akorlar:\n" + "\n".join(lines), None


def _wait_harmonize(path, context):
    from modules.chords import harmonize_melody
    out = tempfile.mktemp(suffix=".mid")
    _, key = harmonize_melody(path, out)
    return f"Tespit edilen ton: {key}. Melodi + akor track'i birlikte.", out


def _wait_mix_analyze(path, context):
    from modules.mix_master import analyze_mix
    wav = convert_to_wav(path)
    result = analyze_mix(wav)
    text = "\n".join(result["suggestions"])
    return text, None


def _wait_mix_compare_1(path, context):
    wav = convert_to_wav(path)
    context.user_data["_ref_wav"] = wav
    context.user_data["mode"] = "mix_compare_2"
    return "Referans kaydını aldım. Şimdi kendi mix'ini gönder.", None


def _wait_mix_compare_2(path, context):
    from modules.mix_master import compare_with_reference
    wav = convert_to_wav(path)
    ref = context.user_data.get("_ref_wav")
    result = compare_with_reference(wav, ref)
    return "\n".join(result["notes"]), None


def _wait_tuner(path, context):
    from modules.tuner import analyze_tuning
    wav = convert_to_wav(path)
    result = analyze_tuning(wav)
    if result is None:
        return "Net bir ses algılayamadım.", None
    return f"En yakın nota: {result['note']} ({result['freq']:.1f} Hz) — {result['verdict']}", None


def _wait_vocal_range(path, context):
    from modules.vocal_range import detect_vocal_range
    wav = convert_to_wav(path)
    result = detect_vocal_range([wav])
    if result is None:
        return "Net bir ses algılayamadım.", None
    return f"Tahmini vokal aralığın: {result['low_note']} — {result['high_note']} ({result['range_semitones']} yarım ton)", None


def _wait_tab_export(path, context):
    from modules.tab_export import midi_to_tab
    text, unplayable = midi_to_tab(path, "gitar")
    return text, None


def _wait_minus_one(path, context):
    from modules.minus_one import remove_center_channel
    out = tempfile.mktemp(suffix=".wav")
    try:
        remove_center_channel(path, out)
    except ValueError as e:
        return str(e), None
    return "Orta kanal (genelde vokal) zayıflatıldı. Not: bu basit bir teknik, Demucs kadar temiz değildir.", out


def _wait_check_sung_note(path, context):
    from modules.solfege_games import check_sung_note
    wav = convert_to_wav(path)
    target = context.user_data.get("_target_note", "C")
    result = check_sung_note(wav, target)
    return result["detail"], None


def _wait_motif_op(op_name):
    def handler(path, context):
        import modules.motif_tools as mt
        out = tempfile.mktemp(suffix=".mid")
        if op_name == "invert":
            mt.invert(path, out)
            msg = "Melodi ilk notaya göre ters çevrildi (inversiyon)."
        elif op_name == "retrograde":
            mt.retrograde(path, out)
            msg = "Melodi tersten (retrograd) çalınıyor."
        elif op_name == "sequence":
            mt.sequence(path, out)
            msg = "Motif, gam içinde kaydırılarak tekrarlandı (sekans)."
        elif op_name == "counter":
            mt.generate_counter_melody(path, out)
            msg = "Ana melodi + basit kontrpuan (karşı ezgi) üretildi."
        return msg, out
    return handler


def _wait_motif_modulation(path, context):
    import modules.motif_tools as mt
    suggestions = mt.suggest_modulation(path)
    return "\n".join(suggestions), None


def _wait_lyrics(path, context):
    return "Bu araç ses değil metin bekliyor — şarkı sözünü (birden fazla satır olabilir) yazıp gönder.", None


def _wait_mic_check(path, context):
    from modules.mic_check import check_recording_quality
    wav = convert_to_wav(path)
    result = check_recording_quality(wav)
    return result["message"], None


WAIT_HANDLERS = {
    "hum_to_midi": _wait_hum_to_midi,
    "poly_to_midi": _wait_poly_to_midi,
    "melody_continue": _wait_melody_continue,
    "chord_detect": _wait_chord_detect,
    "harmonize": _wait_harmonize,
    "mix_analyze": _wait_mix_analyze,
    "mix_compare_1": _wait_mix_compare_1,
    "mix_compare_2": _wait_mix_compare_2,
    "tuner": _wait_tuner,
    "vocal_range": _wait_vocal_range,
    "tab_export": _wait_tab_export,
    "minus_one": _wait_minus_one,
    "check_sung_note": _wait_check_sung_note,
    "motif_invert": _wait_motif_op("invert"),
    "motif_retrograde": _wait_motif_op("retrograde"),
    "motif_sequence": _wait_motif_op("sequence"),
    "motif_counter": _wait_motif_op("counter"),
    "motif_modulation": _wait_motif_modulation,
    "mic_check": _wait_mic_check,
}

WAIT_PROMPTS = {
    "hum_to_midi": "Mırıldan ya da tek sesli çal, sesli mesaj/ses dosyası olarak gönder.",
    "poly_to_midi": "Akorlu/çoklu nota çalışını gönder (deneysel, en iyi sonuç için az sayıda net nota).",
    "melody_continue": "Devamını üretmek istediğim bir .mid dosyası gönder.",
    "chord_detect": "Akorlarını tespit edeceğim ses kaydını gönder.",
    "harmonize": "Armonize edeceğim melodi .mid dosyasını gönder.",
    "mix_analyze": "Analiz edeceğim ses dosyasını gönder.",
    "mix_compare_1": "Önce referans (beğendiğin) kaydı gönder.",
    "mix_compare_2": "Şimdi kendi mix'ini gönder.",
    "tuner": "Akort ölçeceğim kısa bir ses kaydı gönder.",
    "vocal_range": "Rahat söyleyebildiğin en pes ve en tiz notaları içeren bir kayıt gönder.",
    "tab_export": "Tab çıkaracağım .mid dosyasını gönder.",
    "minus_one": "Stereo bir ses dosyası gönder (vokal genelde ortada karılmış olmalı).",
    "check_sung_note": "İstenen notayı söyle, sesli mesaj olarak gönder.",
    "motif_invert": "İnversiyon uygulayacağım motif .mid dosyasını gönder.",
    "motif_retrograde": "Retrograd uygulayacağım motif .mid dosyasını gönder.",
    "motif_sequence": "Sekans uygulayacağım motif .mid dosyasını gönder.",
    "motif_counter": "Karşı ezgi üreteceğim melodi .mid dosyasını gönder.",
    "motif_modulation": "Modülasyon önerisi için bir melodi .mid dosyası gönder.",
    "mic_check": "Kalitesini kontrol edeceğim kısa bir ses kaydı gönder.",
}


# ---------------------------------------------------------------------------
# Anında (buton basılır basılmaz) çalışan aksiyonlar
# ---------------------------------------------------------------------------

async def _handle_immediate_action(query, context, action: str):
    parts = action.split(":")
    kind = parts[0]

    if kind == "mood":
        from modules.chords import suggest_chords_for_mood
        mood = parts[1]
        out = tempfile.mktemp(suffix=".mid")
        chords, _ = suggest_chords_for_mood(mood, "C", out)
        text = f"'{mood}' ruh haline uygun akorlar (C tonunda):\n" + "\n".join(f"{r}: {l}" for r, l in chords)
        await query.message.reply_text(text)
        with open(out, "rb") as f:
            await query.message.reply_document(document=f, filename="akorlar.mid")

    elif kind == "scale":
        from modules.exercises import generate_scale_exercise
        root = parts[1]
        out = tempfile.mktemp(suffix=".mid")
        generate_scale_exercise(root, "major", "başlangıç", out)
        with open(out, "rb") as f:
            await query.message.reply_document(document=f, filename=f"{root}_majör_gam.mid", caption=f"{root} majör gam egzersizi")

    elif kind == "arp":
        from modules.exercises import generate_arpeggio_exercise
        root = parts[1]
        out = tempfile.mktemp(suffix=".mid")
        generate_arpeggio_exercise(root, "maj", "başlangıç", out)
        with open(out, "rb") as f:
            await query.message.reply_document(document=f, filename=f"{root}_arpej.mid", caption=f"{root} majör arpej egzersizi")

    elif kind == "riff":
        from modules.exercises import generate_riff
        root = parts[1]
        out = tempfile.mktemp(suffix=".mid")
        generate_riff(root, "major", "orta", 2, out)
        with open(out, "rb") as f:
            await query.message.reply_document(document=f, filename=f"{root}_riff.mid", caption=f"{root} majör riff")

    elif kind == "game":
        game_type = parts[1]
        if game_type == "interval":
            from modules.solfege_games import make_interval_question
            wav = tempfile.mktemp(suffix=".wav")
            q = make_interval_question(wav)
        elif game_type == "note":
            from modules.solfege_games import make_note_id_question
            wav = tempfile.mktemp(suffix=".wav")
            q = make_note_id_question(wav)
        else:
            from modules.instrument_ear_game import make_timbre_question
            wav = tempfile.mktemp(suffix=".wav")
            q = make_timbre_question(wav)

        buttons = [[InlineKeyboardButton(c, callback_data=f"ans:{c}")] for c in q["choices"]]
        context.user_data["_correct_answer"] = q["correct_answer"]
        with open(wav, "rb") as f:
            await query.message.reply_voice(voice=f)
        await query.message.reply_text("Bu neydi?", reply_markup=InlineKeyboardMarkup(buttons))

    elif kind == "lesson":
        _, topic, idx = parts
        idx = int(idx)
        if topic == "note":
            from modules.note_reading import get_lesson
            lesson = get_lesson(idx)
        else:
            from modules.harmony_theory import get_western_lesson
            lesson = get_western_lesson(idx)
        await query.message.reply_text(f"**{lesson['title']}**\n\n{lesson['text']}")

    elif kind == "quiz":
        quiz_type = parts[1]
        if quiz_type == "note_pos":
            from modules.note_reading import make_note_position_question
            q = make_note_position_question()
        else:
            from modules.harmony_theory import make_chord_function_question
            q = make_chord_function_question("C", "major")
        buttons = [[InlineKeyboardButton(c, callback_data=f"ans:{c}")] for c in q["choices"]]
        context.user_data["_correct_answer"] = q["correct_answer"]
        await query.message.reply_text(q["question"], reply_markup=InlineKeyboardMarkup(buttons))

    elif kind == "makam_intro":
        from modules.harmony_theory import MAKAM_INTRO
        await query.message.reply_text(MAKAM_INTRO)

    elif kind == "drum":
        from modules.studio_backing import generate_drum_pattern
        genre = parts[1]
        out = tempfile.mktemp(suffix=".mid")
        generate_drum_pattern(genre, 4, out)
        with open(out, "rb") as f:
            await query.message.reply_document(document=f, filename=f"{genre}_davul.mid")

    elif kind == "logic":
        from modules.logic_pro_edu import list_topics, get_lesson
        idx = int(parts[1])
        topics = list_topics()
        text = get_lesson(topics[idx])
        await query.message.reply_text(f"**{topics[idx]}**\n\n{text}")

    elif kind == "turkish":
        instrument = parts[1]
        context.user_data["mode"] = f"turkish:{instrument}"
        await query.message.reply_text(
            f"{instrument} sesiyle çalınmasını istediğin bir .mid dosyası gönder.\n\n"
            "Not: bu ses gerçek örnek kayıt değil, basit bir sentez — gerçekçi tını için ileride geliştirilecek."
        )

    elif kind == "template":
        from modules.composition_templates import format_structure
        name = parts[1]
        await query.message.reply_text(format_structure(name))

    elif kind == "backing":
        from modules.improv_backing import generate_backing_loop
        mood, genre = parts[1], parts[2]
        out = tempfile.mktemp(suffix=".mid")
        generate_backing_loop(mood, "C", genre, 2, out)
        with open(out, "rb") as f:
            await query.message.reply_document(document=f, filename=f"backing_{mood}_{genre}.mid")

    elif kind == "coach":
        from modules.progress import suggest_next_practice
        try:
            text = suggest_next_practice(query.from_user.id)
        except Exception as e:
            text = f"Koç önerisi için veritabanı bağlantısı gerekiyor (henüz kurulmamış olabilir). Detay: {e}"
        await query.message.reply_text(text)

    elif kind == "chorddiag":
        from modules.chord_diagrams import guitar_chord_diagram
        root, quality = parts[1], parts[2]
        text = guitar_chord_diagram(root, quality)
        await query.message.reply_text(text or "Bu akor için henüz bir diyagramım yok.")

    elif kind == "daily_challenge":
        from modules.progress import make_daily_challenge
        wav = tempfile.mktemp(suffix=".wav")
        q = make_daily_challenge(wav)
        buttons = [[InlineKeyboardButton(c, callback_data=f"ans:{c}")] for c in q["choices"]]
        context.user_data["_correct_answer"] = q["correct_answer"]
        with open(wav, "rb") as f:
            await query.message.reply_voice(voice=f)
        await query.message.reply_text(f"Günün sorusu ({q['type']}): bu neydi?", reply_markup=InlineKeyboardMarkup(buttons))


# ---------------------------------------------------------------------------
# Telegram handler'ları
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = None
    await update.message.reply_text(
        "Merhaba! Müzik botuna hoş geldin. Ne yapmak istersin?",
        reply_markup=MAIN_MENU,
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    menu = get_menu(key)
    if menu is None:
        await query.edit_message_text("Bu bölüm henüz hazır değil.", reply_markup=MAIN_MENU)
        return
    context.user_data["mode"] = None
    title = "Ne yapmak istersin?" if key == "main" else "Seç:"
    try:
        await query.edit_message_text(title, reply_markup=menu)
    except Exception:
        await query.message.reply_text(title, reply_markup=menu)


async def wait_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data.split(":", 1)[1]
    context.user_data["mode"] = mode
    prompt = WAIT_PROMPTS.get(mode, "Bir dosya gönder.")

    if mode == "check_sung_note":
        import random
        target = random.choice(["C", "D", "E", "F", "G", "A", "B"])
        context.user_data["_target_note"] = target
        prompt = f"{target} notasını söyle ve sesli mesaj olarak gönder."

    await query.message.reply_text(prompt)


async def act_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    try:
        await _handle_immediate_action(query, context, action)
    except Exception:
        logger.exception("Immediate action hatası: %s", action)
        await query.message.reply_text("Bir hata oluştu, tekrar dener misin?")


async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    given = query.data.split(":", 1)[1]
    correct = context.user_data.get("_correct_answer")
    if given == correct:
        await query.edit_message_text(f"✅ Doğru! Cevap: {correct}")
    else:
        await query.edit_message_text(f"❌ Yanlış. Doğru cevap: {correct}, senin cevabın: {given}")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message is None:
        return

    mode = context.user_data.get("mode")

    voice = message.voice or message.audio
    if voice is None and message.document is not None:
        mime = (message.document.mime_type or "")
        name = (message.document.file_name or "")
        if mime.startswith("audio/") or name.lower().endswith((".mp3", ".wav", ".m4a", ".ogg", ".oga", ".flac", ".mid", ".midi")):
            voice = message.document

    if voice is None:
        await message.reply_text("Bir ses dosyası, sesli mesaj ya da .mid dosyası göndermelisin.")
        return

    if not mode:
        await message.reply_text("Önce menüden ne yapmak istediğini seçmelisin.", reply_markup=MAIN_MENU)
        return

    await message.reply_text("Alındı, işleniyor... 🎧")

    tg_file = await context.bot.get_file(voice.file_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "girdi_dosya")
        await tg_file.download_to_drive(input_path)

        try:
            if mode.startswith("turkish:"):
                from modules.turkish_instruments import render_midi_to_instrument
                instrument = mode.split(":", 1)[1]
                out = tempfile.mktemp(suffix=".wav")
                render_midi_to_instrument(input_path, out, instrument)
                await message.reply_text(f"{instrument} tınısıyla seslendirildi (basit sentez, yer tutucu).")
                with open(out, "rb") as f:
                    await message.reply_voice(voice=f)
                return

            handler = WAIT_HANDLERS.get(mode)
            if handler is None:
                await message.reply_text("Bu işlem için henüz bir işleyici yok.", reply_markup=MAIN_MENU)
                return

            text, out_path = handler(input_path, context)
            await message.reply_text(text)
            if out_path:
                ext = os.path.splitext(out_path)[1]
                filename = f"sonuc{ext}"
                with open(out_path, "rb") as f:
                    if ext in (".mid", ".midi"):
                        await message.reply_document(document=f, filename=filename)
                    else:
                        await message.reply_voice(voice=f) if ext in (".ogg", ".oga") else await message.reply_document(document=f, filename=filename)

        except Exception as e:
            logger.error("İşleme hatası (mode=%s): %s\n%s", mode, e, traceback.format_exc())
            await message.reply_text(f"Bir hata oluştu, tekrar dener misin? (Detay: {e})")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message is None or not message.text:
        return

    mode = context.user_data.get("mode")
    if mode == "lyrics":
        from modules.lyrics_tools import check_rhyme_scheme
        lines = message.text.split("\n")
        scheme, analysis = check_rhyme_scheme(lines)
        reply_lines = [f"Kafiye şeması: {scheme}"]
        for a in analysis:
            reply_lines.append(f"({a['syllables']} hece) {a['line']}")
        await message.reply_text("\n".join(reply_lines))
        return

    # varsayılan: menüye yönlendir
    await message.reply_text("Ne yapmak istersin?", reply_markup=MAIN_MENU)


def main():
    threading.Thread(target=_start_health_server, daemon=True).start()
    logger.info("Sağlık kontrolü (health check) sunucusu başlatıldı.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu:"))
    app.add_handler(CallbackQueryHandler(wait_callback, pattern="^wait:"))
    app.add_handler(CallbackQueryHandler(act_callback, pattern="^act:"))
    app.add_handler(CallbackQueryHandler(answer_callback, pattern="^ans:"))
    app.add_handler(
        MessageHandler(
            filters.VOICE | filters.AUDIO | filters.Document.AUDIO | filters.Document.FileExtension("mid"),
            handle_file,
        )
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot başlatılıyor (polling modu)...")
    app.run_polling()


if __name__ == "__main__":
    main()
