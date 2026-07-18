"""
Beste araçları: motif geliştirme (inversiyon, retrograd, augmentasyon/diminüsyon,
sekans), basit kontrpuan (karşı ezgi) üretici, modülasyon (tonalite değişimi) önerici.
Hepsi klasik kompozisyon tekniklerine dayanan, kural tabanlı, deterministik araçlar.
"""

from core.midi_utils import read_midi_notes, write_midi, MidiNote
from core.music_theory import scale_notes, estimate_key, NOTE_NAMES, SCALES


def _load(input_midi_path):
    notes = read_midi_notes(input_midi_path)
    if not notes:
        raise ValueError("Motif boş.")
    return notes


def invert(input_midi_path, output_midi_path):
    """Melodiyi ilk notaya göre ters çevirir (yukarı giden aralık aşağı gider)."""
    notes = _load(input_midi_path)
    axis = notes[0][0]
    new_notes = [MidiNote(pitch=max(0, min(127, 2 * axis - p)), start=s, end=e, velocity=90) for p, s, e in notes]
    write_midi([new_notes], output_midi_path)
    return output_midi_path


def retrograde(input_midi_path, output_midi_path):
    """Melodiyi tersten (sondan başa) çalar, ritim de tersine döner."""
    notes = _load(input_midi_path)
    total_end = max(e for _, _, e in notes)
    new_notes = []
    for p, s, e in notes:
        new_s = total_end - e
        new_e = total_end - s
        new_notes.append(MidiNote(pitch=p, start=new_s, end=new_e, velocity=90))
    new_notes.sort(key=lambda n: n.start)
    write_midi([new_notes], output_midi_path)
    return output_midi_path


def augment(input_midi_path, output_midi_path, factor=2.0):
    """Tüm nota sürelerini (ve aralarındaki boşlukları) factor ile çarpar
    (>1 augmentasyon/yavaşlatma, <1 diminüsyon/hızlandırma)."""
    notes = _load(input_midi_path)
    new_notes = [MidiNote(pitch=p, start=s * factor, end=e * factor, velocity=90) for p, s, e in notes]
    write_midi([new_notes], output_midi_path)
    return output_midi_path


def transpose(input_midi_path, output_midi_path, semitones):
    notes = _load(input_midi_path)
    new_notes = [MidiNote(pitch=max(0, min(127, p + semitones)), start=s, end=e, velocity=90) for p, s, e in notes]
    write_midi([new_notes], output_midi_path)
    return output_midi_path


def sequence(input_midi_path, output_midi_path, scale_degree_shift=2, repetitions=3):
    """Motifi, tespit edilen gam içinde art arda (her seferinde bir miktar
    kaydırarak) tekrar eden klasik bir 'sekans' oluşturur."""
    notes = _load(input_midi_path)
    hist = [0.0] * 12
    for p, s, e in notes:
        hist[p % 12] += max(e - s, 0.01)
    root_pc, scale_name = estimate_key(hist)
    scale_pcs = scale_notes(root_pc, scale_name)
    n_deg = len(scale_pcs)

    def pitch_to_degree(p):
        octave = p // 12
        pc = p % 12
        best_i, best_d = 0, 99
        for i, spc in enumerate(scale_pcs):
            d = min((pc - spc) % 12, (spc - pc) % 12)
            if d < best_d:
                best_d, best_i = d, i
        return octave * n_deg + best_i

    def degree_to_pitch(deg):
        octv, idx = divmod(deg, n_deg)
        return octv * 12 + scale_pcs[idx]

    motif_len = notes[-1][2] - notes[0][1]
    all_notes = []
    for rep in range(repetitions):
        shift = rep * scale_degree_shift
        offset_t = rep * motif_len
        for p, s, e in notes:
            deg = pitch_to_degree(p) + shift
            new_pitch = max(0, min(127, degree_to_pitch(deg)))
            all_notes.append(MidiNote(pitch=new_pitch, start=s - notes[0][1] + offset_t, end=e - notes[0][1] + offset_t, velocity=90))

    write_midi([all_notes], output_midi_path)
    return output_midi_path


def generate_counter_melody(input_midi_path, output_midi_path):
    """
    Basit kontrpuan: ana melodiye, her nota için (kontrpuan kurallarına yakın)
    3'lü ya da 6'lı aralıkta, aynı gam içinde bir karşı ezgi üretir. Paralel
    5'li/8'liden kaçınmaya çalışır (ardışık aynı aralık tekrarını kısıtlar).
    Dürüstlük notu: tam bir species counterpoint motoru değil, basitleştirilmiş
    ve pratik bir yaklaşım.
    """
    notes = _load(input_midi_path)
    hist = [0.0] * 12
    for p, s, e in notes:
        hist[p % 12] += max(e - s, 0.01)
    root_pc, scale_name = estimate_key(hist)
    scale_pcs = scale_notes(root_pc, scale_name)
    n_deg = len(scale_pcs)

    def pitch_to_degree(p):
        octave = p // 12
        pc = p % 12
        best_i, best_d = 0, 99
        for i, spc in enumerate(scale_pcs):
            d = min((pc - spc) % 12, (spc - pc) % 12)
            if d < best_d:
                best_d, best_i = d, i
        return octave * n_deg + best_i

    def degree_to_pitch(deg):
        octv, idx = divmod(deg, n_deg)
        return octv * 12 + scale_pcs[idx]

    counter = []
    last_interval_degrees = None
    for p, s, e in notes:
        deg = pitch_to_degree(p)
        # tercihen 3'lü (2 gam derecesi) alt taraftan, ardışık aynı aralık
        # (paralel hareket) olursa 6'lıya (5 derece) geç
        interval_degrees = -2
        if last_interval_degrees == interval_degrees:
            interval_degrees = -5
        counter_deg = deg + interval_degrees
        counter_pitch = max(0, min(127, degree_to_pitch(counter_deg)))
        counter.append(MidiNote(pitch=counter_pitch, start=s, end=e, velocity=75))
        last_interval_degrees = interval_degrees

    melody_notes = [MidiNote(pitch=p, start=s, end=e, velocity=95) for p, s, e in notes]
    write_midi([melody_notes, counter], output_midi_path)
    return output_midi_path


def suggest_modulation(input_midi_path):
    """
    Mevcut tonu tespit edip, klasik pivot-akor modülasyon hedefleri önerir:
    5. derece (dominant), 4. derece (subdominant), ve paralel majör/minör.
    Ses üretmez, sadece metin önerisi döner (bot bunu mesaj olarak gösterir).
    """
    notes = _load(input_midi_path)
    hist = [0.0] * 12
    for p, s, e in notes:
        hist[p % 12] += max(e - s, 0.01)
    root_pc, scale_name = estimate_key(hist)
    root_name = NOTE_NAMES[root_pc]

    dominant_pc = (root_pc + 7) % 12
    subdominant_pc = (root_pc + 5) % 12
    relative_pc = (root_pc + 9) % 12 if scale_name == "major" else (root_pc + 3) % 12
    relative_name = "minör" if scale_name == "major" else "majör"

    suggestions = [
        f"Mevcut ton: {root_name} {scale_name}",
        f"Dominant tona (V) modülasyon: {NOTE_NAMES[dominant_pc]} — en doğal/yumuşak geçiş, ortak akor olarak mevcut V veya VII akorunu pivot kullan",
        f"Subdominant tona (IV) modülasyon: {NOTE_NAMES[subdominant_pc]} — sakin, geriye dönük bir renk katar",
        f"Paralel {relative_name} tona modülasyon: {NOTE_NAMES[relative_pc]} — aynı tondan (relative key) yumuşak geçiş, tonik akoru ortak kullanılabilir",
    ]
    return suggestions
