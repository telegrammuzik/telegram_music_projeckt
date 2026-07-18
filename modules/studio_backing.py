"""
Faz 8: Stüdyo altyapı üretimi — tür bazlı davul paterni ve akorlardan otomatik
bas hattı üretimi. Kural tabanlı kalıp kütüphanesi (Magenta gibi eğitilmiş bir
groove modeli değil — dürüstlük notu: bu basit ama kullanışlı, sabit kalıplara
dayanıyor).
"""

from core.midi_utils import write_midi, MidiNote
from core.music_theory import NOTE_NAMES, CHORD_TEMPLATES

# GM davul haritası (kanal 9/10, standart notalar)
KICK = 36
SNARE = 38
CLOSED_HAT = 42
OPEN_HAT = 46

# 16'lık adımlarla (1 bar = 16 adım), tür bazlı davul kalıpları
DRUM_PATTERNS = {
    "pop": {
        KICK:  [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,0],
        SNARE: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        CLOSED_HAT: [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1],
    },
    "rock": {
        KICK:  [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0],
        SNARE: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        CLOSED_HAT: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
    },
    "trap": {
        KICK:  [1,0,0,0, 0,0,0,1, 0,0,1,0, 0,0,0,0],
        SNARE: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        CLOSED_HAT: [1,1,1,1, 1,1,1,1, 1,1,1,0, 1,1,1,1],
    },
    "akustik": {
        KICK:  [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
        SNARE: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        CLOSED_HAT: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
    },
}


def generate_drum_pattern(genre: str, bars: int, output_midi_path: str, tempo_bpm: int = 100):
    if genre not in DRUM_PATTERNS:
        raise ValueError(f"Bilinmeyen tür: {genre}. Seçenekler: {list(DRUM_PATTERNS.keys())}")

    pattern = DRUM_PATTERNS[genre]
    step_dur = 60.0 / tempo_bpm / 4  # 16'lık nota süresi

    notes = []
    for bar in range(bars):
        for instrument, steps in pattern.items():
            for i, hit in enumerate(steps):
                if hit:
                    t = (bar * 16 + i) * step_dur
                    notes.append(MidiNote(pitch=instrument, start=t, end=t + step_dur * 0.9, velocity=100, channel=9))

    write_midi([notes], output_midi_path, tempo_bpm=tempo_bpm)
    return output_midi_path, len(notes)


def generate_bassline_from_chords(chord_sequence, output_midi_path: str, tempo_bpm: int = 100, pattern: str = "root_fifth"):
    """
    chord_sequence: [(root_pc, quality, duration_beats), ...]
    pattern: "root_fifth" (kök-beşli) veya "walking" (basit yürüyen bas)
    """
    beat_dur = 60.0 / tempo_bpm
    notes = []
    t = 0.0

    for root_pc, quality, dur_beats in chord_sequence:
        base = 36 - (36 % 12) + root_pc  # bas oktavı (C2 civarı)
        intervals = CHORD_TEMPLATES.get(quality, [0, 4, 7])
        fifth = intervals[2] if len(intervals) > 2 else 7

        if pattern == "root_fifth":
            half = dur_beats / 2
            notes.append(MidiNote(pitch=base, start=t, end=t + half * beat_dur * 0.9, velocity=100))
            notes.append(MidiNote(pitch=base + fifth, start=t + half * beat_dur, end=t + dur_beats * beat_dur * 0.9, velocity=95))
        else:  # walking — kök, 3lü, 5li, oktav
            steps = [0, intervals[1] if len(intervals) > 1 else 4, fifth, 12]
            each = dur_beats / len(steps)
            for i, iv in enumerate(steps):
                st = t + i * each * beat_dur
                notes.append(MidiNote(pitch=base + iv, start=st, end=st + each * beat_dur * 0.9, velocity=90))

        t += dur_beats * beat_dur

    write_midi([notes], output_midi_path, tempo_bpm=tempo_bpm)
    return output_midi_path, len(notes)
