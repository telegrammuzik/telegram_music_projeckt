"""
Faz 2: Var olan bir melodinin (MIDI) devamını üretir.

Dürüstlük notu: Bu, Magenta/Music Transformer gibi eğitilmiş bir derin öğrenme
modeli DEĞİL — böyle bir model indirmek/çalıştırmak network erişimi ve ekstra
kaynak gerektiriyor, bu ortamda kurulamıyor. Bunun yerine, melodinin kendi
notalarından basit bir istatistiksel model (1. derece Markov zinciri, gam
adımı cinsinden) çıkarıp, tespit edilen tona (gama) sadık kalarak makul bir
devam üretiyoruz. Kural tabanlı ama müzikal olarak tutarlı bir sonuç hedefler;
"akıllı" bir yapay zekanın yaratıcılığını iddia etmez.
"""

import random

from core.midi_utils import read_midi_notes, write_midi, MidiNote
from core.music_theory import scale_notes, estimate_key

DEFAULT_STEP_WEIGHTS = {
    -2: 1, -1: 4, 0: 2, 1: 4, 2: 1, 3: 1, -3: 1,
}


def _pitch_to_scale_degree(pitch, root_pc, scale_pcs):
    """Bir MIDI notasını en yakın gam derecesine (indeks) ve oktava çözer."""
    octave = pitch // 12
    pc = pitch % 12
    # en yakın gam üyesini bul
    best_idx, best_dist = 0, 99
    for idx, spc in enumerate(scale_pcs):
        dist = min((pc - spc) % 12, (spc - pc) % 12)
        if dist < best_dist:
            best_dist, best_idx = dist, idx
    return octave * len(scale_pcs) + best_idx


def _scale_degree_to_pitch(degree, root_pc, scale_pcs):
    n = len(scale_pcs)
    octave = degree // n
    idx = degree % n
    return octave * 12 + scale_pcs[idx]


def continue_melody(input_midi_path: str, output_midi_path: str, num_notes: int = 16, seed=None):
    """
    Dönüş: (output_midi_path, orijinal_nota_sayisi, uretilen_nota_sayisi, tespit_edilen_ton)
    """
    rng = random.Random(seed)
    notes = read_midi_notes(input_midi_path)  # [(pitch, start, end), ...]

    if len(notes) < 2:
        raise ValueError("Devamını üretmek için en az 2 notalık bir melodi gerekiyor.")

    # 1) Ton tespiti (pitch-class histogramı süreye göre ağırlıklı)
    hist = [0.0] * 12
    for pitch, s, e in notes:
        hist[pitch % 12] += max(e - s, 0.01)
    root_pc, scale_name = estimate_key(hist)
    scale_pcs = scale_notes(root_pc, scale_name)

    # 2) Notaları gam derecesine çevir, ardışık derece farklarından (adımlardan)
    # basit bir geçiş modeli (histogram) çıkar
    degrees = [_pitch_to_scale_degree(p, root_pc, scale_pcs) for p, _, _ in notes]
    steps = [degrees[i + 1] - degrees[i] for i in range(len(degrees) - 1)]

    step_weights = dict(DEFAULT_STEP_WEIGHTS)
    if steps:
        observed = {}
        for s in steps:
            observed[s] = observed.get(s, 0) + 1
        # gözlemlenen adımlara daha fazla ağırlık ver, ama varsayılanları da koru (Laplace smoothing benzeri)
        for s, count in observed.items():
            step_weights[s] = step_weights.get(s, 1) + count * 3

    step_choices = list(step_weights.keys())
    step_probs = list(step_weights.values())

    # 3) Ritim: girdi melodisindeki nota sürelerini döngüsel olarak tekrar kullan
    durations = [e - s for _, s, e in notes]
    gaps = [notes[i + 1][1] - notes[i][2] for i in range(len(notes) - 1)]
    avg_gap = max(sum(gaps) / len(gaps), 0.0) if gaps else 0.02

    # 4) Devamı üret
    current_degree = degrees[-1]
    t = notes[-1][2] + avg_gap
    generated = []
    for i in range(num_notes):
        step = rng.choices(step_choices, weights=step_probs, k=1)[0]
        current_degree += step
        pitch = _scale_degree_to_pitch(current_degree, root_pc, scale_pcs)
        pitch = max(36, min(96, pitch))  # makul enstrüman aralığında tut

        dur = durations[i % len(durations)]
        # son notayı tonike (I derecesi) yaklaştırarak "bitmiş" hissi ver
        if i == num_notes - 1:
            tonic_degree = (current_degree // len(scale_pcs)) * len(scale_pcs)
            pitch = _scale_degree_to_pitch(tonic_degree, root_pc, scale_pcs)
            pitch = max(36, min(96, pitch))  # ayni sinirlama burda da uygulanmali

        # current_degree sınırsız gezinebilir (adımlar birikir); pitch'i her
        # tur kırpıyoruz ama derece referansı da gerçek pitch'e senkron kalsın
        # diye, kırpma devreye girdiyse dereceyi de kırpılmış pitch'e göre
        # sıfırlıyoruz (yoksa sonraki adımlar hâlâ aşırı uçtaki bir dereceden
        # devam edip sürekli sınıra yaslanabilirdi)
        current_degree = _pitch_to_scale_degree(pitch, root_pc, scale_pcs)

        generated.append(MidiNote(pitch=pitch, start=t, end=t + dur, velocity=85))
        t += dur + avg_gap

    # 5) Orijinal + devamı aynı dosyada, ayrı iki "track" (kanal) olarak yaz
    # (Orijinal kanal 0, devam kanal 1 — DAW'da ayrı ayrı görülüp istenirse
    # sessize alınabilir/renklendirilebilir)
    original_notes = [MidiNote(pitch=p, start=s, end=e, velocity=90) for p, s, e in notes]

    write_midi([original_notes, generated], output_midi_path)

    key_label = f"{['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][root_pc]} {scale_name}"
    return output_midi_path, len(notes), len(generated), key_label
