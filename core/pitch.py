"""
Ortak pitch (frekans) tespiti — otokorelasyon tabanlı, sadece numpy. Faz 1
(hum_to_midi) kendi içinde ayrı bir kopyasını taşıyor (dokunup bozmamak için);
tuner, vocal_range gibi YENİ modüller bu paylaşılan sürümü kullanıyor.
"""

import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def autocorr_pitch(frame, sr, fmin=70, fmax=1000):
    frame = frame - np.mean(frame)
    energy = np.sum(frame ** 2)
    if energy < 1e-9:
        return 0.0, 0.0
    windowed = frame * np.hanning(len(frame))
    ac = np.correlate(windowed, windowed, mode="full")
    ac = ac[len(ac) // 2:]
    if ac[0] <= 0:
        return 0.0, 0.0
    min_lag = int(sr / fmax)
    max_lag = min(int(sr / fmin), len(ac) - 1)
    if min_lag >= max_lag:
        return 0.0, 0.0
    segment = ac[min_lag:max_lag]
    peak_idx = int(np.argmax(segment))
    lag = min_lag + peak_idx
    confidence = float(segment[peak_idx] / ac[0])
    freq = sr / lag if lag > 0 else 0.0
    return freq, confidence


def hz_to_note_and_cents(freq):
    """Frekansı en yakın notaya ve o nottan sapmayı (cent, -50..+50) döner."""
    if freq <= 0:
        return None, 0, 0
    midi_float = 69 + 12 * np.log2(freq / 440.0)
    nearest = int(round(midi_float))
    cents = (midi_float - nearest) * 100
    name = f"{NOTE_NAMES[nearest % 12]}{nearest // 12 - 1}"
    return name, nearest, cents


def analyze_pitch_track(y, sr, frame_length=2048, hop_length=512, fmin=70, fmax=1000):
    """Tüm sinyal üzerinde kare kare pitch takibi yapar, (times, freqs, confs) döner."""
    freqs, confs, times = [], [], []
    for start in range(0, max(len(y) - frame_length, 1), hop_length):
        frame = y[start:start + frame_length]
        f, c = autocorr_pitch(frame, sr, fmin, fmax)
        freqs.append(f)
        confs.append(c)
        times.append(start / sr)
    return np.array(times), np.array(freqs), np.array(confs)
