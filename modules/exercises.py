"""
Faz 4: Enstrüman egzersizleri — gam, arpej ve basit riff kalıpları üretir.
Kural tabanlı, tamamen deterministik (rastgele değil) müzik teorisinden
üretiliyor; metronom için sabit bir ritim ızgarası kullanılıyor.
"""

import random

from core.music_theory import SCALES, CHORD_TEMPLATES, NOTE_NAMES
from core.midi_utils import write_midi, MidiNote

LEVELS = {
    "başlangıç": {"note_dur": 0.5, "octaves": 1},
    "orta": {"note_dur": 0.3, "octaves": 2},
    "ileri": {"note_dur": 0.18, "octaves": 3},
}


def generate_scale_exercise(root_name: str, scale_name: str, level: str, output_midi_path: str):
    cfg = LEVELS[level]
    root_pc = NOTE_NAMES.index(root_name)
    intervals = SCALES[scale_name]  # ham, artan aralıklar (ör. majör: 0,2,4,5,7,9,11)
    base = 60 - (60 % 12) + root_pc  # kök notanın C5 civarındaki ilk oktavı

    pitches = []
    for octv in range(cfg["octaves"]):
        for iv in intervals:
            pitches.append(base + octv * 12 + iv)
    pitches.append(base + cfg["octaves"] * 12)  # tepe (oktav) notaya dokun
    pitches = pitches + pitches[::-1][1:]  # geri iniş

    notes = []
    t = 0.0
    for p in pitches:
        notes.append(MidiNote(pitch=p, start=t, end=t + cfg["note_dur"] * 0.95, velocity=95))
        t += cfg["note_dur"]

    write_midi([notes], output_midi_path)
    return output_midi_path, len(notes)


def generate_arpeggio_exercise(root_name: str, quality: str, level: str, output_midi_path: str):
    cfg = LEVELS[level]
    root_pc = NOTE_NAMES.index(root_name)
    intervals = CHORD_TEMPLATES[quality]  # ham, artan aralıklar (ör. maj: 0,4,7)
    base = 60 - (60 % 12) + root_pc

    pitches = []
    for octv in range(cfg["octaves"]):
        for iv in intervals:
            pitches.append(base + octv * 12 + iv)
    pitches += pitches[::-1][1:]

    notes = []
    t = 0.0
    for p in pitches:
        notes.append(MidiNote(pitch=p, start=t, end=t + cfg["note_dur"] * 0.95, velocity=95))
        t += cfg["note_dur"]

    write_midi([notes], output_midi_path)
    return output_midi_path, len(notes)


def generate_riff(root_name: str, scale_name: str, level: str, bars: int, output_midi_path: str, seed=None):
    """Basit, gam-içi rastgele ama ritmik olarak ızgaraya oturan bir riff üretir."""
    rng = random.Random(seed)
    cfg = LEVELS[level]
    root_pc = NOTE_NAMES.index(root_name)
    intervals = SCALES[scale_name]  # ham, artan aralıklar (gam içindeki basamak sayısı = len(intervals))
    base = 60 - (60 % 12) + root_pc

    notes_per_bar = 8
    total_notes = bars * notes_per_bar
    note_dur = cfg["note_dur"]
    n_degrees = len(intervals)

    current_degree_idx = 0
    notes = []
    t = 0.0
    for i in range(total_notes):
        step = rng.choice([-2, -1, -1, 0, 1, 1, 2])
        current_degree_idx = max(0, min(n_degrees * cfg["octaves"] - 1, current_degree_idx + step))
        octv, idx = divmod(current_degree_idx, n_degrees)
        pitch = base + octv * 12 + intervals[idx]
        notes.append(MidiNote(pitch=pitch, start=t, end=t + note_dur * 0.9, velocity=rng.randint(80, 100)))
        t += note_dur

    write_midi([notes], output_midi_path)
    return output_midi_path, len(notes)
