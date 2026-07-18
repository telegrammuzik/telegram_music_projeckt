"""
Faz 3: Akor tespiti (sesten) ve akor üretimi (melodiden / ruh halinden).

Dürüstlük notu — sesten akor tespiti: madmom/BTC gibi gerçek şarkı verisiyle
eğitilmiş derin öğrenme modelleri bu ortamda kurulamıyor (ağ erişimi yok).
Burada klasik bir MIR (müzik bilgi çıkarımı) yöntemi olan "chroma + şablon
eşleştirme" kullanılıyor (numpy FFT ile kendi chromagram'ımızı çıkarıp, 24 majör/
minör + birkaç 7'li şablonla karşılaştırıyoruz). Bu yöntem temel triadlarda
gayet iyi, ama çok yoğun prodüksiyonlu/gürültülü kayıtlarda madmom/BTC kadar
isabetli değildir — dürüst beklenti: "iyi bir ilk tahmin", "kesin doğru" değil.
"""

import numpy as np

from core.wav_io import load_wav_mono
from core.music_theory import NOTE_NAMES, scale_notes, estimate_key, diatonic_chords, roman_to_chord, chord_pitches, MOOD_PROGRESSIONS
from core.midi_utils import write_midi, MidiNote, read_midi_notes

FRAME_LENGTH = 4096
HOP_LENGTH = 2048

# Chord şablonları: pitch-class ağırlıkları (kök=0 referansla, sonra 12 kere döndürülüyor)
_TEMPLATE_INTERVALS = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "7": [0, 4, 7, 10],
    "min7": [0, 3, 7, 10],
    "maj7": [0, 4, 7, 11],
    "dim": [0, 3, 6],
}


def _build_templates():
    templates = {}
    for quality, intervals in _TEMPLATE_INTERVALS.items():
        for root in range(12):
            vec = np.zeros(12)
            for iv in intervals:
                vec[(root + iv) % 12] = 1.0
            templates[(root, quality)] = vec / np.linalg.norm(vec)
    return templates


_TEMPLATES = _build_templates()


def _chroma_from_audio(y, sr):
    """Basit bir chromagram: her kare için FFT büyüklüğünü 12 pitch-class'a katlar."""
    n_frames = max((len(y) - FRAME_LENGTH) // HOP_LENGTH + 1, 0)
    freqs = np.fft.rfftfreq(FRAME_LENGTH, d=1.0 / sr)
    # her FFT bin'ini pitch-class'a haritalayan tablo (bir kere hesapla)
    with np.errstate(divide="ignore"):
        midi_bins = 69 + 12 * np.log2(np.maximum(freqs, 1e-6) / 440.0)
    pc_bins = np.mod(np.round(midi_bins), 12).astype(int)
    valid_bins = (freqs >= 60) & (freqs <= 5000)

    chroma = np.zeros((n_frames, 12))
    window = np.hanning(FRAME_LENGTH)
    times = []
    for i in range(n_frames):
        start = i * HOP_LENGTH
        frame = y[start:start + FRAME_LENGTH] * window
        mag = np.abs(np.fft.rfft(frame))
        for pc in range(12):
            mask = valid_bins & (pc_bins == pc)
            chroma[i, pc] = mag[mask].sum()
        times.append(start / sr)

    return chroma, np.array(times)


def detect_chords_from_audio(wav_path: str, detailed: bool = False):
    """
    detailed=False ("temiz mod"): daha uzun pencere, sadece emin akorlar.
    detailed=True ("detaylı mod"): daha kısa pencere, ara/geçiş akorlarını da yakalamaya çalışır.
    Dönüş: [(chord_label, start_sec, end_sec), ...]
    """
    y, sr = load_wav_mono(wav_path, target_sr=22050)
    chroma, times = _chroma_from_audio(y, sr)

    if len(chroma) == 0:
        return []

    smooth_window = 2 if detailed else 5
    if smooth_window > 1 and len(chroma) > smooth_window:
        kernel = np.ones(smooth_window) / smooth_window
        chroma = np.array([np.convolve(chroma[:, pc], kernel, mode="same") for pc in range(12)]).T

    labels = []
    for frame in chroma:
        norm = np.linalg.norm(frame)
        if norm < 1e-9:
            labels.append(None)
            continue
        frame_n = frame / norm
        best_score, best_chord = -1, None
        for (root, quality), template in _TEMPLATES.items():
            score = float(np.dot(frame_n, template))
            if score > best_score:
                best_score, best_chord = score, (root, quality)
        labels.append(best_chord if best_score > 0.5 else None)

    # ardışık aynı etiketleri birleştir
    segments = []
    current = None
    seg_start = 0.0
    for t, lab in zip(times, labels):
        if lab != current:
            if current is not None:
                segments.append((current, seg_start, t))
            current, seg_start = lab, t
    if current is not None:
        segments.append((current, seg_start, times[-1] + (times[1] - times[0] if len(times) > 1 else 0.5)))

    min_dur = 0.15 if detailed else 0.4
    segments = [s for s in segments if s[0] is not None and (s[2] - s[1]) >= min_dur]

    result = []
    for (root, quality), s, e in segments:
        label = f"{NOTE_NAMES[root]}{'' if quality == 'maj' else quality if quality != 'min' else 'm'}"
        result.append((label, s, e))
    return result


def suggest_chords_for_mood(mood: str, root_name: str = "C", output_midi_path: str = None):
    """Ruh haline göre hazır bir akor ilerlemesi üretir (Faz 3 eklentisi)."""
    if mood not in MOOD_PROGRESSIONS:
        raise ValueError(f"Bilinmeyen ruh hali: {mood}. Seçenekler: {list(MOOD_PROGRESSIONS.keys())}")

    root_pc = NOTE_NAMES.index(root_name)
    options = MOOD_PROGRESSIONS[mood]
    scale_name, romans = options[0]

    chords_out = []
    notes = []
    t = 0.0
    bar_dur = 2.0
    for roman in romans:
        chord_root, quality = roman_to_chord(root_pc, scale_name, roman)
        pitches = chord_pitches(chord_root, quality, octave=4)
        for p in pitches:
            notes.append(MidiNote(pitch=p, start=t, end=t + bar_dur, velocity=80))
        label = f"{NOTE_NAMES[chord_root]}{'' if quality == 'maj' else quality if quality != 'min' else 'm'}"
        chords_out.append((roman, label))
        t += bar_dur

    if output_midi_path:
        write_midi([notes], output_midi_path)

    return chords_out, output_midi_path


def harmonize_melody(input_midi_path: str, output_midi_path: str):
    """Bir melodinin altına, tespit edilen tona göre basit diyatonik akorlar üretir
    (her ~1 saniyelik pencerede en uygun diyatonik akoru seçer)."""
    notes = read_midi_notes(input_midi_path)
    if not notes:
        raise ValueError("Melodi boş.")

    hist = [0.0] * 12
    for pitch, s, e in notes:
        hist[pitch % 12] += max(e - s, 0.01)
    root_pc, scale_name = estimate_key(hist)
    diatonic = diatonic_chords(root_pc, scale_name)

    total_end = max(e for _, _, e in notes)
    window = 1.5
    chord_notes = []
    t = 0.0
    while t < total_end:
        window_end = t + window
        window_hist = [0.0] * 12
        for pitch, s, e in notes:
            overlap = min(e, window_end) - max(s, t)
            if overlap > 0:
                window_hist[pitch % 12] += overlap

        best_score, best = -1, diatonic[0]
        for chord_root, quality in diatonic:
            template_pcs = {(chord_root + iv) % 12 for iv in _TEMPLATE_INTERVALS[quality]}
            score = sum(window_hist[pc] for pc in template_pcs)
            if score > best_score:
                best_score, best = score, (chord_root, quality)

        for p in chord_pitches(best[0], best[1], octave=3):
            chord_notes.append(MidiNote(pitch=p, start=t, end=window_end, velocity=70))
        t = window_end

    melody_notes = [MidiNote(pitch=p, start=s, end=e, velocity=95) for p, s, e in notes]
    write_midi([melody_notes, chord_notes], output_midi_path)

    key_label = f"{NOTE_NAMES[root_pc]} {scale_name}"
    return output_midi_path, key_label
