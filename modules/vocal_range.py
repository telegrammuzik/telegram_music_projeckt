"""
Ek: Vokal aralığı tespiti. Bir veya birkaç kayıttan en pes ve en tiz güvenilir
şekilde algılanan notaları bulur. İleride bu bilgi, üretilen melodi/akorları
kullanıcının rahat aralığına otomatik transpoze etmek için kullanılacak
(bkz. roadmap "Vokal aralığı tespiti ve otomatik tona uyarlama").
"""

import numpy as np

from core.wav_io import load_wav_mono
from core.pitch import analyze_pitch_track, hz_to_note_and_cents


def detect_vocal_range(wav_paths):
    """wav_paths: bir veya birden fazla ses dosyası yolu (liste)."""
    all_midi_nums = []

    for path in wav_paths:
        y, sr = load_wav_mono(path, target_sr=22050)
        _, freqs, confs = analyze_pitch_track(y, sr)
        valid = (confs > 0.4) & (freqs > 0)
        for f in freqs[valid]:
            _, midi_num, _ = hz_to_note_and_cents(f)
            all_midi_nums.append(midi_num)

    if not all_midi_nums:
        return None

    # aşırı uçtaki (muhtemelen hatalı) birkaç değeri budamak için 5-95 persentil kullan
    low = int(np.percentile(all_midi_nums, 5))
    high = int(np.percentile(all_midi_nums, 95))

    low_name, _, _ = hz_to_note_and_cents(440.0 * 2 ** ((low - 69) / 12))
    high_name, _, _ = hz_to_note_and_cents(440.0 * 2 ** ((high - 69) / 12))

    return {"low_note": low_name, "high_note": high_name, "low_midi": low, "high_midi": high, "range_semitones": high - low}


def suggest_transpose_semitones(vocal_range, melody_low_midi, melody_high_midi):
    """Bir melodinin, tespit edilen vokal aralığına sığması için gereken transpoze miktarını önerir."""
    if vocal_range is None:
        return 0
    melody_center = (melody_low_midi + melody_high_midi) / 2
    range_center = (vocal_range["low_midi"] + vocal_range["high_midi"]) / 2
    return int(round(range_center - melody_center))
