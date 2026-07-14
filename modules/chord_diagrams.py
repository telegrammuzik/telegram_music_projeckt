"""
Ek: Akor parmak pozisyonu/voicing diyagramları (gitar/piyano). Metin tabanlı
(ASCII) gösterim — grafik/görsel değil ama Telegram'da hızlıca okunabilir.
Küçük, elle hazırlanmış bir kütüphane (en yaygın açık pozisyon akorları);
her akor/kalite kombinasyonu için değil, en çok kullanılanlar için.
"""

GUITAR_CHORD_SHAPES = {
    ("C", "maj"): "x32010",
    ("A", "maj"): "x02220",
    ("G", "maj"): "320003",
    ("D", "maj"): "xx0232",
    ("E", "maj"): "022100",
    ("F", "maj"): "133211",
    ("A", "min"): "x02210",
    ("D", "min"): "xx0231",
    ("E", "min"): "022000",
    ("C", "min"): "x35543",
    ("G", "min"): "355333",
    ("B", "min"): "x24432",
    ("A", "7"): "x02020",
    ("D", "7"): "xx0212",
    ("E", "7"): "020100",
    ("G", "7"): "320001",
    ("C", "7"): "x32310",
}


def guitar_chord_diagram(root_name: str, quality: str):
    shape = GUITAR_CHORD_SHAPES.get((root_name, quality))
    if shape is None:
        return None
    strings = "EADGBe"
    lines = [f"{root_name}{'' if quality=='maj' else quality if quality!='min' else 'm'} (gitar, açık pozisyon)"]
    for s, fret in zip(strings, shape):
        lines.append(f"{s}: {'kapalı' if fret=='x' else ('açık' if fret=='0' else f'{fret}. perde')}")
    return "\n".join(lines)


def piano_chord_diagram(root_pc: int, quality: str):
    from core.music_theory import CHORD_TEMPLATES, NOTE_NAMES
    intervals = CHORD_TEMPLATES[quality]
    names = [NOTE_NAMES[(root_pc + iv) % 12] for iv in intervals]
    label = f"{NOTE_NAMES[root_pc]}{'' if quality=='maj' else quality if quality!='min' else 'm'}"
    return f"{label} (piyano): {' - '.join(names)} tuşlarına aynı anda bas"
