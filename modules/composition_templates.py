"""
Ek: Kompozisyon şablonları — hazır şarkı yapısı iskeletleri (kaç bar,
hangi bölüm). Kullanıcı mırıldandığı fikirleri bu şablona yerleştirerek
şarkısını organize edebilir.
"""

SONG_STRUCTURES = {
    "pop_standart": [
        ("Intro", 4), ("Verse", 8), ("Pre-Chorus", 4), ("Chorus", 8),
        ("Verse", 8), ("Pre-Chorus", 4), ("Chorus", 8), ("Bridge", 4),
        ("Chorus", 8), ("Outro", 4),
    ],
    "basit_pop": [
        ("Intro", 4), ("Verse", 8), ("Chorus", 8), ("Verse", 8), ("Chorus", 8), ("Outro", 4),
    ],
    "balad": [
        ("Intro", 4), ("Verse", 8), ("Chorus", 8), ("Verse", 8), ("Chorus", 8),
        ("Bridge", 8), ("Chorus", 8), ("Outro", 4),
    ],
    "12_bar_blues": [
        ("A", 4), ("A", 4), ("B", 4),
    ],
}


def get_structure(name):
    if name not in SONG_STRUCTURES:
        raise ValueError(f"Bilinmeyen şablon: {name}. Seçenekler: {list(SONG_STRUCTURES.keys())}")
    return SONG_STRUCTURES[name]


def format_structure(name):
    structure = get_structure(name)
    total_bars = sum(bars for _, bars in structure)
    lines = [f"{section} ({bars} bar)" for section, bars in structure]
    return f"Toplam {total_bars} bar:\n" + "\n".join(lines)
