"""
Ek: Basit dijital akort aleti (tuner). Kullanıcı kısa bir ses kaydı gönderir,
bot en baskın/kararlı frekansı bulup en yakın notayı ve kaç cent (yüzde perde)
kadar pes/tiz olduğunu söyler. Gerçek zamanlı sürekli gösterge DEĞİL — Telegram
bot mimarisinin doğal sınırı (bkz. roadmap "Platform Stratejisi" notu).
"""

import numpy as np

from core.wav_io import load_wav_mono
from core.pitch import analyze_pitch_track, hz_to_note_and_cents


def analyze_tuning(wav_path: str):
    y, sr = load_wav_mono(wav_path, target_sr=22050)
    times, freqs, confs = analyze_pitch_track(y, sr)

    valid = (confs > 0.4) & (freqs > 0)
    if not valid.any():
        return None

    # en güvenilir karelerin medyan frekansını al (tek bir anlık değere göre değil)
    best_freqs = freqs[valid]
    median_freq = float(np.median(best_freqs))

    name, midi_num, cents = hz_to_note_and_cents(median_freq)
    if abs(cents) < 5:
        verdict = "tam akortta"
    elif cents > 0:
        verdict = f"{abs(cents):.0f} cent tiz (biraz düşür)"
    else:
        verdict = f"{abs(cents):.0f} cent pes (biraz yükselt)"

    return {"note": name, "freq": median_freq, "cents": cents, "verdict": verdict}
