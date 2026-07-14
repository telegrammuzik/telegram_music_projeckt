"""
Faz 11: Türk müziği çalgıları ses sentezi (tulum, zurna, klasik kemençe, kabak
kemane, kaval, ney vb.).

Dürüstlük notu — bu ÖNEMLİ: Gerçek DDSP tabanlı "neural timbre transfer" (birkaç
dakikalık örnek kayıttan çalgının gerçek tınısını öğrenme) bu ortamda kurulamıyor
— hem network erişimi hem de eğitim verisi (gerçek tulum/zurna kayıtları) gerekiyor,
ikisi de burada yok. Bu modül şu an sadece basit bir ADDİTİF SENTEZ (birkaç
harmonik bileşeni farklı ağırlıklarla toplama) kullanıyor — her çalgıya "biraz
farklı" bir karakter veriyor ama GERÇEK çalgı sesini taklit ETMİYOR. Bunu bir
yer tutucu (placeholder) olarak düşün: buton/menü akışı ve MIDI->ses boru hattı
hazır, ama gerçekçi tını için ileride gerçek örnek kayıtlar (SoundFont ya da
DDSP eğitim verisi) eklenmesi gerekiyor (roadmap'te not edildi).
"""

import wave
import numpy as np

from core.midi_utils import read_midi_notes

SAMPLE_RATE = 22050

# Her "çalgı" için basit harmonik ağırlıklar (1. harmonik = temel frekans) ve
# zarf (envelope) karakteri — gerçek çalgı fiziğini modellemiyor, sadece
# farklı çalgılar arasında duyulabilir bir tını farkı yaratmayı hedefliyor.
INSTRUMENT_PROFILES = {
    "tulum": {"harmonics": [1.0, 0.6, 0.4, 0.3, 0.2, 0.15], "attack": 0.05, "release": 0.05, "drone": True},
    "zurna": {"harmonics": [1.0, 0.8, 0.7, 0.5, 0.4, 0.3, 0.2], "attack": 0.01, "release": 0.02, "drone": False},
    "klasik_kemençe": {"harmonics": [1.0, 0.5, 0.3, 0.2, 0.1], "attack": 0.03, "release": 0.08, "drone": False},
    "kabak_kemane": {"harmonics": [1.0, 0.45, 0.25, 0.15, 0.1], "attack": 0.04, "release": 0.1, "drone": False},
    "kaval": {"harmonics": [1.0, 0.3, 0.15, 0.05], "attack": 0.04, "release": 0.05, "drone": False},
    "ney": {"harmonics": [1.0, 0.25, 0.35, 0.1, 0.05], "attack": 0.08, "release": 0.1, "drone": False},
}


def _synth_note(freq, duration, profile, sr=SAMPLE_RATE):
    n = max(int(duration * sr), 1)
    t = np.linspace(0, duration, n, endpoint=False)
    wave_sig = np.zeros(n)
    for h_idx, weight in enumerate(profile["harmonics"], start=1):
        wave_sig += weight * np.sin(2 * np.pi * freq * h_idx * t)
    wave_sig /= sum(profile["harmonics"])

    attack_n = max(int(profile["attack"] * sr), 1)
    release_n = max(int(profile["release"] * sr), 1)
    envelope = np.ones(n)
    envelope[:attack_n] = np.linspace(0, 1, attack_n)
    if release_n < n:
        envelope[-release_n:] = np.linspace(1, 0, release_n)

    # hafif nefes/yay gürültüsü (reed/yay çalgılarına biraz doku katmak için)
    noise = np.random.default_rng(0).normal(0, 0.02, n)

    return wave_sig * envelope + noise * envelope


def render_midi_to_instrument(input_midi_path: str, output_wav_path: str, instrument: str):
    if instrument not in INSTRUMENT_PROFILES:
        raise ValueError(f"Bilinmeyen çalgı: {instrument}. Seçenekler: {list(INSTRUMENT_PROFILES.keys())}")

    profile = INSTRUMENT_PROFILES[instrument]
    notes = read_midi_notes(input_midi_path)
    if not notes:
        raise ValueError("MIDI'de nota yok.")

    total_dur = max(e for _, _, e in notes) + 0.5
    buffer = np.zeros(int(total_dur * SAMPLE_RATE) + SAMPLE_RATE)

    for pitch, start, end in notes:
        freq = 440.0 * 2 ** ((pitch - 69) / 12)
        dur = max(end - start, 0.05)
        sig = _synth_note(freq, dur, profile)
        start_sample = int(start * SAMPLE_RATE)
        end_sample = start_sample + len(sig)
        if end_sample > len(buffer):
            buffer = np.pad(buffer, (0, end_sample - len(buffer)))
        buffer[start_sample:end_sample] += sig

    peak = np.max(np.abs(buffer))
    if peak > 0:
        buffer = buffer / peak * 0.9

    int16 = np.clip(buffer * 32767, -32768, 32767).astype(np.int16)
    w = wave.open(output_wav_path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SAMPLE_RATE)
    w.writeframes(int16.tobytes())
    w.close()

    return output_wav_path
