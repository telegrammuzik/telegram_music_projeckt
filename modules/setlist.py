"""
Ek: Set listesi oluşturucu. Şarkı listesi (isim, ton, tempo) verildiğinde,
tempo/ton geçişleri kulağa rahat gelecek şekilde bir sıralama önerir — ani
ton sıçramalarından kaçınıp (yakın tonlar/quintler çemberi mantığı) ve
tempo akışını (yavaştan hızlıya kademeli ya da enerjiyi koruyacak şekilde) göz önünde tutar.
"""

from core.music_theory import NOTE_NAMES

CIRCLE_OF_FIFTHS = ["C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#", "F"]


def _key_distance(key1, key2):
    i1 = CIRCLE_OF_FIFTHS.index(key1)
    i2 = CIRCLE_OF_FIFTHS.index(key2)
    diff = abs(i1 - i2)
    return min(diff, 12 - diff)


def build_setlist(songs, start_song=None):
    """
    songs: [{"name": str, "key": "C", "tempo": 120}, ...]
    Basit bir açgözlü (greedy) algoritma: her adımda, mevcut şarkıya en yakın
    tonda ve tempo farkı en az olan bir sonraki şarkıyı seçer.
    """
    remaining = list(songs)
    if not remaining:
        return []

    if start_song:
        current = next((s for s in remaining if s["name"] == start_song), remaining[0])
    else:
        current = remaining[0]
    remaining.remove(current)
    order = [current]

    while remaining:
        def score(s):
            key_dist = _key_distance(current["key"], s["key"])
            tempo_dist = abs(current["tempo"] - s["tempo"]) / 20.0
            return key_dist + tempo_dist

        next_song = min(remaining, key=score)
        remaining.remove(next_song)
        order.append(next_song)
        current = next_song

    return order


def format_setlist(order):
    lines = []
    for i, s in enumerate(order, 1):
        lines.append(f"{i}. {s['name']} — {s['key']}, {s['tempo']} BPM")
    return "\n".join(lines)
