"""
Ek: Doğaçlama partneri / backing loop üretici. Seçilen ton+ruh haline göre
akorlardan bas+ritim eşliğinde dönen bir loop üretir (chords.py + studio_backing.py'yi birleştirir).
"""

import tempfile
import os

from core.music_theory import NOTE_NAMES, roman_to_chord
from modules.chords import MOOD_PROGRESSIONS
from modules.studio_backing import generate_drum_pattern, generate_bassline_from_chords
from core.midi_utils import write_midi, read_midi_notes, MidiNote


def generate_backing_loop(mood: str, root_name: str, genre: str, repeats: int, output_midi_path: str, tempo_bpm: int = 100):
    if mood not in MOOD_PROGRESSIONS:
        raise ValueError(f"Bilinmeyen ruh hali: {mood}")

    root_pc = NOTE_NAMES.index(root_name)
    scale_name, romans = MOOD_PROGRESSIONS[mood][0]

    chord_sequence = []
    for _ in range(repeats):
        for roman in romans:
            chord_root, quality = roman_to_chord(root_pc, scale_name, roman)
            chord_sequence.append((chord_root, quality, 4))  # her akor 4 vuruş (1 bar, 4/4)

    bars = len(chord_sequence)  # her akor 1 bar sayılıyor (4 vuruş = 1 bar 4/4'te)

    # Geçici dosyalarda ayrı üret, sonra tek MIDI'de birleştir. tempfile ile
    # her çağrı için benzersiz dosya adı kullanıyoruz — sunucuda aynı anda
    # birden fazla kullanıcı bu fonksiyonu çağırırsa çakışma olmasın diye.
    drums_tmp = tempfile.mktemp(suffix="_drums.mid")
    bass_tmp = tempfile.mktemp(suffix="_bass.mid")
    try:
        generate_drum_pattern(genre, bars, drums_tmp, tempo_bpm=tempo_bpm)
        generate_bassline_from_chords(chord_sequence, bass_tmp, tempo_bpm=tempo_bpm)

        drum_notes = [MidiNote(pitch=p, start=s, end=e, velocity=100, channel=9) for p, s, e in read_midi_notes(drums_tmp)]
        bass_notes = [MidiNote(pitch=p, start=s, end=e, velocity=95) for p, s, e in read_midi_notes(bass_tmp)]
    finally:
        for f in (drums_tmp, bass_tmp):
            if os.path.exists(f):
                os.remove(f)

    write_midi([drum_notes, bass_notes], output_midi_path, tempo_bpm=tempo_bpm)
    return output_midi_path, len(chord_sequence)
