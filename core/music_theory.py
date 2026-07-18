"""
Ortak müzik teorisi araçları (Faz 0): gamlar, akor şablonları, ton (key) tespiti,
diyatonik akor üretimi, hazır akor ilerlemesi kütüphanesi. Faz 3 (akorlar),
Faz 4 (egzersizler), Faz 7 (armoni), Faz 8 (backing), Beste araçları bunu paylaşır.
"""

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
}

# Akor şablonları: kök nottan itibaren yarım ton aralıkları
CHORD_TEMPLATES = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dim7": [0, 3, 6, 9],
    "sus4": [0, 5, 7],
    "sus2": [0, 2, 7],
}

# Majör gamda diyatonik akor kaliteleri (derece: I..VII)
MAJOR_DIATONIC_QUALITIES = ["maj", "min", "min", "maj", "maj", "min", "dim"]
MINOR_DIATONIC_QUALITIES = ["min", "dim", "maj", "min", "min", "maj", "maj"]

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]

# Ruh haline göre akor ilerlemesi kütüphanesi (roman rakamlarıyla, majör/minör bağlamında)
MOOD_PROGRESSIONS = {
    "mutlu": [("major", ["I", "V", "VI", "IV"]), ("major", ["I", "IV", "V", "I"])],
    "hüzünlü": [("natural_minor", ["I", "VI", "III", "VII"]), ("natural_minor", ["I", "IV", "V", "I"])],
    "epik": [("natural_minor", ["I", "VII", "VI", "VII"]), ("harmonic_minor", ["I", "IV", "V", "I"])],
    "nostaljik": [("major", ["VI", "IV", "I", "V"])],
    "lofi": [("major", ["II", "V", "I", "VI"]), ("dorian", ["I", "IV", "I", "IV"])],
    "gerilim": [("harmonic_minor", ["I", "V", "I", "V"])],
}


def scale_notes(root_pc: int, scale_name: str):
    """root_pc: 0-11 (C=0). Dönüş: gamdaki pitch class'lar (0-11 arası, artan)."""
    intervals = SCALES[scale_name]
    return [(root_pc + i) % 12 for i in intervals]


def diatonic_chords(root_pc: int, scale_name: str):
    """Verilen ton/gam için 7 diyatonik akoru (kök pc, kalite) listesi olarak döner."""
    notes = scale_notes(root_pc, scale_name)
    qualities = MAJOR_DIATONIC_QUALITIES if scale_name in ("major", "mixolydian", "dorian") else MINOR_DIATONIC_QUALITIES
    return [(notes[i], qualities[i % len(qualities)]) for i in range(7)]


def roman_to_chord(root_pc: int, scale_name: str, roman: str):
    """'V', 'IV' gibi roman rakamını (root_pc, quality) akoruna çevirir."""
    idx = ROMAN.index(roman.upper())
    chords = diatonic_chords(root_pc, scale_name)
    return chords[idx]


def chord_pitches(root_pc: int, quality: str, octave: int = 4):
    """Akorun gerçek MIDI nota numaralarını döner (tek oktavda, kapalı pozisyon)."""
    base = (octave + 1) * 12 + root_pc
    return [base + i for i in CHORD_TEMPLATES[quality]]


def estimate_key(pitch_classes_histogram):
    """
    Basit bir ton tespiti: 12 elemanlı bir pitch-class histogramı (her notanın
    ne kadar çaldığı/ne kadar süre) alır, Krumhansl-Schmuckler'in basitleştirilmiş
    haliyle (gam üyeliği ağırlıklı korelasyon) en olası (root_pc, 'major'/'natural_minor')
    tonunu döner.
    """
    best_score = -1
    best = (0, "major")
    for root in range(12):
        for scale_name in ("major", "natural_minor"):
            members = set(scale_notes(root, scale_name))
            score = sum(pitch_classes_histogram[pc] for pc in members)
            if score > best_score:
                best_score = score
                best = (root, scale_name)
    return best


def note_name_to_pc(name: str) -> int:
    flat_map = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    name = flat_map.get(name, name)
    return NOTE_NAMES.index(name)
