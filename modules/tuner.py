"""
Ek: Dijital akort aleti (tuner). Kullanıcı kısa bir ses kaydı gönderir, bot
en baskın/kararlı frekansı bulup en yakın notayı, kaç cent (yüzde perde)
pes/tiz olduğunu söyler ve görsel bir ibre/gösterge (PNG) üretir. Gerçek
zamanlı sürekli gösterge DEĞİL — Telegram bot mimarisinin doğal sınırı.

v2 notu: önceki sürüm sadece düz metin döndürüyordu ve pitch tespiti
alt-sample hassasiyetsizdi (core/pitch.py'de düzeltildi — parabolik
interpolasyon + oktav-hata düzeltmesi eklendi). Bu sürüm ayrıca en kararlı
(en sık tekrar eden notaya ait) frekans kümesini seçiyor — nefes/gürültü
kaynaklı tek tük sapan kareleri artık dışlıyor.
"""

import numpy as np

from core.wav_io import load_wav_mono
from core.pitch import analyze_pitch_track, hz_to_note_and_cents


def analyze_tuning(wav_path: str):
    y, sr = load_wav_mono(wav_path, target_sr=22050)
    times, freqs, confs = analyze_pitch_track(y, sr)

    valid = (confs > 0.45) & (freqs > 0)
    if not valid.any():
        return None

    best_freqs = freqs[valid]

    # en kararlı bölgeyi bul: her kareyi en yakın notaya yuvarla, en sık
    # görülen notaya ait frekansların medyanını al (ara geçiş/titreşen
    # karelerin sonucu bozmasını engeller)
    midi_estimates = np.round(69 + 12 * np.log2(best_freqs / 440.0)).astype(int)
    values, counts = np.unique(midi_estimates, return_counts=True)
    dominant_note = values[np.argmax(counts)]
    stable_freqs = best_freqs[midi_estimates == dominant_note]
    target_freq = float(np.median(stable_freqs))

    name, midi_num, cents = hz_to_note_and_cents(target_freq)
    if abs(cents) < 5:
        verdict = "tam akortta"
    elif cents > 0:
        verdict = f"{abs(cents):.0f} cent tiz (biraz düşür)"
    else:
        verdict = f"{abs(cents):.0f} cent pes (biraz yükselt)"

    stability = float(len(stable_freqs)) / max(len(best_freqs), 1)

    return {
        "note": name, "freq": target_freq, "cents": cents, "verdict": verdict,
        "stability": stability,
    }


def render_tuner_gauge_png(result: dict, output_png_path: str):
    """Cent sapmasını -50..+50 aralığında yarım daire bir ibre olarak çizer."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cents = max(-50, min(50, result["cents"]))
    fig, ax = plt.subplots(figsize=(4, 2.6), subplot_kw={"aspect": "equal"})

    theta = np.linspace(np.pi, 0, 200)
    ax.plot(np.cos(theta), np.sin(theta), color="black", linewidth=2)

    for tick_cents in range(-50, 51, 10):
        angle = np.pi * (1 - (tick_cents + 50) / 100)
        x0, y0 = 0.92 * np.cos(angle), 0.92 * np.sin(angle)
        x1, y1 = 1.0 * np.cos(angle), 1.0 * np.sin(angle)
        color = "green" if tick_cents == 0 else "black"
        ax.plot([x0, x1], [y0, y1], color=color, linewidth=2 if tick_cents == 0 else 1)

    needle_angle = np.pi * (1 - (cents + 50) / 100)
    ax.plot([0, 0.85 * np.cos(needle_angle)], [0, 0.85 * np.sin(needle_angle)],
            color="red", linewidth=3, zorder=5)
    ax.add_patch(plt.Circle((0, 0), 0.03, color="black", zorder=6))

    ax.text(0, -0.25, f"{result['note']}  ({result['freq']:.1f} Hz)", ha="center", fontsize=13, weight="bold")
    ax.text(0, -0.45, result["verdict"], ha="center", fontsize=11)
    ax.text(-1.05, -0.05, "pes", ha="center", fontsize=9)
    ax.text(1.05, -0.05, "tiz", ha="center", fontsize=9)

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.6, 1.15)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_png_path, dpi=130, facecolor="white")
    plt.close(fig)
    return output_png_path
