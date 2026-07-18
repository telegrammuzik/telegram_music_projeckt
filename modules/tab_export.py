"""
Ek: MIDI'den gitar/bas tab çıktısı. Basitleştirilmiş bir yaklaşım kullanır:
her nota için, standart akortta (E A D G B E) mümkün olan en düşük pozisyonlu
tel/perde kombinasyonunu seçer (gerçek bir tab yazılımı kadar "çalınabilirlik"
optimizasyonu yapmaz, ama doğru nota ve mantıklı bir pozisyon verir).
"""

from core.midi_utils import read_midi_notes

GUITAR_STANDARD_TUNING = [40, 45, 50, 55, 59, 64]  # E2 A2 D3 G3 B3 E4 (tel 6->1)
BASS_STANDARD_TUNING = [28, 33, 38, 43]  # E1 A1 D2 G2


def _best_string_fret(pitch, tuning, max_fret=15):
    options = []
    for string_idx, open_pitch in enumerate(tuning):
        fret = pitch - open_pitch
        if 0 <= fret <= max_fret:
            options.append((string_idx, fret))
    if not options:
        return None
    # tercihen düşük perde (daha kolay pozisyon)
    return min(options, key=lambda x: x[1])


def midi_to_tab(input_midi_path, instrument="gitar"):
    notes = read_midi_notes(input_midi_path)
    tuning = GUITAR_STANDARD_TUNING if instrument == "gitar" else BASS_STANDARD_TUNING
    n_strings = len(tuning)

    lines = [[] for _ in range(n_strings)]
    unplayable = 0

    for pitch, s, e in notes:
        result = _best_string_fret(pitch, tuning)
        if result is None:
            unplayable += 1
            continue
        string_idx, fret = result
        for i in range(n_strings):
            if i == string_idx:
                lines[i].append(f"{fret:>2}")
            else:
                lines[i].append(" -")

    string_names = ["e", "B", "G", "D", "A", "E"] if instrument == "gitar" else ["G", "D", "A", "E"]
    # yüksek telden (ince) düşük tele doğru göster (geleneksel tab gösterimi)
    tab_text_lines = []
    for i in reversed(range(n_strings)):
        tab_text_lines.append(f"{string_names[n_strings - 1 - i]}|{'-'.join(lines[i])}-|")

    header = f"({instrument} tab, standart akort)\n"
    return header + "\n".join(tab_text_lines), unplayable
