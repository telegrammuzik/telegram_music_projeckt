"""
Ortak MIDI -> ses önizleme (Faz 0 eklentisi). Botun ürettiği HER .mid dosyası
artık aynı zamanda sentezlenmiş bir .wav önizlemesiyle birlikte gönderiliyor —
böylece telefondan (DAW açmadan) dinlenebiliyor.

Dürüstlük notu: Gerçek bir piyano/enstrüman örnek kaydı (SoundFont/sample
library) DEĞİL — bu ortamda indirilebilecek güvenilir bir soundfont kaynağı
doğrulanamadığı için (ve Render'ın ücretsiz planında ekstra ağırlık riski
almamak için) yine numpy tabanlı bir sentez kullanıyoruz. Ama artık düz sinüs
değil: çok-harmonikli + hafif inharmonicity + üstel sönümlü bir "elektrikli
piyano/rhodes tarzı" ton — MIDI'yi olduğu gibi dinlemekten çok daha kullanışlı,
ama gerçek bir piyano kaydıyla karıştırılmamalı.
"""

import wave
import numpy as np

from core.midi_utils import read_midi_notes

SAMPLE_RATE = 22050

# Elektro-piyano benzeri harmonik yapı: temel + birkaç üst harmonik, hafif
# inharmonicity (gerçek tellerin/tine'ların tam katları olmayan üst kısımları)
_HARMONICS = [1.0, 0.5, 0.28, 0.16, 0.09, 0.05, 0.03]
_INHARMONICITY = [0.0, 0.002, 0.006, 0.012, 0.02, 0.03, 0.045]


def _note_wave(freq, duration, velocity=90, sr=SAMPLE_RATE):
    n = max(int(duration * sr), 1)
    t = np.linspace(0, duration, n, endpoint=False)
    sig = np.zeros(n)
    for (h_idx, weight), inharm in zip(enumerate(_HARMONICS, start=1), _INHARMONICITY):
        h_freq = freq * h_idx * (1 + inharm)
        sig += weight * np.sin(2 * np.pi * h_freq * t)
    sig /= sum(_HARMONICS)

    # hızlı atak, üstel sönüm (piyano/rhodes karakteri — vurgu sonrası kararlı
    # bir sustain yerine sürekli azalan bir genlik)
    attack_n = max(int(0.004 * sr), 1)
    env = np.ones(n)
    env[:attack_n] = np.linspace(0, 1, attack_n)
    decay_rate = 2.2 + (1.0 - velocity / 127.0)  # düşük velocity biraz daha hızlı söner
    env *= np.exp(-decay_rate * t / max(duration, 0.05))

    vel_gain = 0.5 + 0.5 * (velocity / 127.0)
    return sig * env * vel_gain


def render_preview(input_midi_path: str, output_wav_path: str, velocity_default: int = 95):
    notes = read_midi_notes(input_midi_path)
    if not notes:
        raise ValueError("MIDI'de nota yok, önizleme üretilemedi.")

    total = max(e for _, _, e in notes) + 1.2
    buffer = np.zeros(int(total * SAMPLE_RATE) + SAMPLE_RATE)

    for pitch, s, e in notes:
        freq = 440.0 * 2 ** ((pitch - 69) / 12)
        dur = max(e - s, 0.08) + 0.5  # kısa bir release kuyruğu ekle
        sig = _note_wave(freq, dur, velocity=velocity_default)
        start_sample = int(s * SAMPLE_RATE)
        end_sample = start_sample + len(sig)
        if end_sample > len(buffer):
            buffer = np.pad(buffer, (0, end_sample - len(buffer)))
        buffer[start_sample:end_sample] += sig * 0.7

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
