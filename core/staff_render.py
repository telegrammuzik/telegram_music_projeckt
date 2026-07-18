"""
Ortak porte (staff) görselleştirme (Faz 0 eklentisi). music21/LilyPond gibi
gerçek notasyon motorları network gerektirdiği için kurulamadı, ama matplotlib
bu ortamda mevcut — bu yüzden 5 çizgili gerçek bir porte + nota başları + ledger
line'ları elle çiziyoruz. Görsel değil sadece metin olan eski sürümden çok daha
kullanışlı: artık egzersizler ve nota okuma oyunlarında GERÇEK bir porte
görseli gönderilebiliyor.

Basitleştirme notu: nota yazımı (spelling) için her zaman diyez (#) kullanılıyor
(bemol/anahtar bazlı doğru yazım yok) — bu görsel/eğitim amaçlı bir basitleştirme,
profesyonel bir notasyon motoru kadar "doğru" değil ama konum ve nota adını
doğru gösteriyor.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

NATURAL_FOR_PC = {
    0: ("C", False), 1: ("C", True), 2: ("D", False), 3: ("D", True),
    4: ("E", False), 5: ("F", False), 6: ("F", True), 7: ("G", False),
    8: ("G", True), 9: ("A", False), 10: ("A", True), 11: ("B", False),
}
LETTER_STEP = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _pitch_to_y(midi_pitch, clef="treble"):
    """Bir MIDI notasının porte üzerindeki dikey konumunu (staff-space birimi)
    hesaplar. Treble (sol anahtarı): alt çizgi = E4. Bass (fa anahtarı): alt çizgi = G2."""
    pc = midi_pitch % 12
    octave = midi_pitch // 12 - 1
    letter, sharp = NATURAL_FOR_PC[pc]
    absolute_step = octave * 7 + LETTER_STEP[letter]
    baseline_step = (4 * 7 + LETTER_STEP["E"]) if clef == "treble" else (2 * 7 + LETTER_STEP["G"])
    y = (absolute_step - baseline_step) * 0.5
    return y, sharp


def _ledger_positions(y):
    positions = []
    if y > 4.01:
        pos = 5
        while pos <= y + 0.01:
            positions.append(pos)
            pos += 1
    elif y < -0.01:
        pos = -1
        while pos >= y - 0.01:
            positions.append(pos)
            pos -= 1
    return positions


def render_staff_png(pitches, output_png_path, clef="treble", title=None, labels=None):
    """pitches: MIDI nota numaraları listesi (soldan sağa sırayla çizilir).
    labels: (opsiyonel) her nota için altına yazılacak küçük etiket listesi."""
    n = max(len(pitches), 1)
    width = max(2.5, 0.9 * n + 1.5)
    fig, ax = plt.subplots(figsize=(width, 3.2))

    for i in range(5):
        ax.plot([0, n + 1], [i, i], color="black", linewidth=1.2, zorder=1)

    for idx, pitch in enumerate(pitches):
        x = idx + 1
        y, sharp = _pitch_to_y(pitch, clef=clef)

        for pos in _ledger_positions(y):
            ax.plot([x - 0.5, x + 0.5], [pos, pos], color="black", linewidth=1.2, zorder=4)

        ax.add_patch(Ellipse((x, y), 0.62, 0.42, angle=-15, color="black", zorder=3))
        if abs(y) > 2.4:
            stem_dir = -1 if y > 0 else 1
        else:
            stem_dir = -1
        stem_top = y + stem_dir * 1.6
        ax.plot([x + (0.3 if stem_dir == -1 else -0.3), x + (0.3 if stem_dir == -1 else -0.3)],
                [y, stem_top], color="black", linewidth=1.0, zorder=2)

        if sharp:
            ax.text(x - 0.55, y, "♯", fontsize=13, va="center", ha="center", zorder=4)

        if labels and idx < len(labels):
            ax.text(x, -3.2, labels[idx], fontsize=9, ha="center", va="center")

    clef_label = "Sol Anahtarı" if clef == "treble" else "Fa Anahtarı"

    ax.set_xlim(-0.5, n + 1.5)
    ax.set_ylim(-4.0, 6.5)
    ax.axis("off")
    full_title = f"{clef_label}" + (f" — {title}" if title else "")
    ax.set_title(full_title, fontsize=11)
    fig.tight_layout()
    fig.savefig(output_png_path, dpi=130, transparent=False, facecolor="white")
    plt.close(fig)
    return output_png_path
