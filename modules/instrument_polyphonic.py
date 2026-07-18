"""
Faz 1 eklentisi: Enstrümanla çalınan AKORLU/çoklu nota (polifonik) kayıtları
MIDI'ye çevirir (piyano akoru, gitar strumming vb.).

Dürüstlük notu — ÖNEMLİ: Spotify'ın Basic Pitch'i (roadmap'te bahsedilen,
gerçek eğitilmiş model) bu ortamda kurulamıyor (ağ erişimi yok). Bunun yerine
basit bir "FFT'de birden fazla tepe (peak) noktası bul" yöntemi kullanılıyor
— bu, net çalınmış, az sayıda (2-4) nota içeren akorlarda makul çalışır ama
Basic Pitch kadar isabetli değildir; yoğun/gürültülü kayıtlarda hatalı ekstra
notalar (harmonik karışıklığı) üretebilir. Tek nota (monofonik) çalışlar için
hâlâ hum_to_midi.py kullanılmalı, o çok daha güvenilir.
"""

import numpy as np

from core.wav_io import load_wav_mono
from core.midi_utils import write_midi, MidiNote

FRAME_LENGTH = 4096
HOP_LENGTH = 1024
MAX_SIMULTANEOUS_NOTES = 4
MIN_PEAK_RATIO = 0.15  # en güçlü tepenin bu oranından zayıf tepeler elenir
MIN_NOTE_DURATION = 0.1
MAX_GAP_FRAMES = 2


def _find_peaks(magnitude, freqs, fmin=60, fmax=1200):
    valid = (freqs >= fmin) & (freqs <= fmax)
    mag = magnitude.copy()
    mag[~valid] = 0

    peaks = []
    for i in range(2, len(mag) - 2):
        if mag[i] > mag[i - 1] and mag[i] > mag[i + 1] and mag[i] > mag[i - 2] and mag[i] > mag[i + 2]:
            peaks.append((freqs[i], mag[i]))

    if not peaks:
        return []

    peaks.sort(key=lambda x: -x[1])
    top_mag = peaks[0][1]
    peaks = [p for p in peaks if p[1] >= top_mag * MIN_PEAK_RATIO]
    return peaks[:MAX_SIMULTANEOUS_NOTES]


def _hz_to_midi(freq):
    return int(round(69 + 12 * np.log2(freq / 440.0)))


def _transcribe_with_basic_pitch(wav_path: str, output_midi_path: str):
    """Basic Pitch, polifonik/akorlu kayıtlarda buradaki naif FFT-peak-picking
    yönteminden ÇOK daha iyi sonuç verir (asıl tasarlandığı senaryo budur).
    requirements.txt'e eklendi ama bu ortamda kurulup test EDİLEMEDİ — Render'da
    ilk kez gerçek anlamda çalışacak. Başarısız olursa None döner, aşağıdaki
    naif yönteme otomatik düşülür (bot çökmez)."""
    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
    except Exception:
        return None
    try:
        _, midi_data, _ = predict(wav_path, model_or_model_path=ICASSP_2022_MODEL_PATH)
        midi_data.write(output_midi_path)
        note_count = sum(len(inst.notes) for inst in midi_data.instruments)
        return output_midi_path, note_count
    except Exception:
        return None


def transcribe_polyphonic(wav_path: str, output_midi_path: str):
    bp_result = _transcribe_with_basic_pitch(wav_path, output_midi_path)
    if bp_result is not None and bp_result[1] > 0:
        return bp_result
    return _transcribe_polyphonic_naive(wav_path, output_midi_path)


def _transcribe_polyphonic_naive(wav_path: str, output_midi_path: str):
    """Basic Pitch mevcut değilse/başarısız olursa devreye giren, önceden
    sentetik akorlarla test edilmiş naif FFT-peak-picking yedeği."""
    y, sr = load_wav_mono(wav_path, target_sr=22050)
    if len(y) <= FRAME_LENGTH:
        write_midi([[]], output_midi_path)
        return output_midi_path, 0

    freqs = np.fft.rfftfreq(FRAME_LENGTH, d=1.0 / sr)
    window = np.hanning(FRAME_LENGTH)

    active = {}  # pitch -> (start_time, last_seen_frame_idx)
    finished_notes = []
    frame_idx = 0

    for start in range(0, len(y) - FRAME_LENGTH, HOP_LENGTH):
        t = start / sr
        frame = y[start:start + FRAME_LENGTH] * window
        mag = np.abs(np.fft.rfft(frame))
        peaks = _find_peaks(mag, freqs)
        detected_pitches = {_hz_to_midi(f) for f, _ in peaks if f > 0}

        # devam eden notaları güncelle / kapat
        for pitch in list(active.keys()):
            if pitch in detected_pitches:
                active[pitch] = (active[pitch][0], frame_idx)
            elif frame_idx - active[pitch][1] > MAX_GAP_FRAMES:
                start_t, last_frame = active.pop(pitch)
                end_t = t
                if end_t - start_t >= MIN_NOTE_DURATION:
                    finished_notes.append((pitch, start_t, end_t))

        # yeni tespit edilen notaları başlat
        for pitch in detected_pitches:
            if pitch not in active:
                active[pitch] = (t, frame_idx)

        frame_idx += 1

    end_t = len(y) / sr
    for pitch, (start_t, _) in active.items():
        if end_t - start_t >= MIN_NOTE_DURATION:
            finished_notes.append((pitch, start_t, end_t))

    midi_notes = [MidiNote(pitch=max(0, min(127, p)), start=s, end=e, velocity=90) for p, s, e in finished_notes]
    write_midi([midi_notes], output_midi_path)
    return output_midi_path, len(midi_notes)
