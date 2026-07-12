"""
Faz 1 (v1 — monofonik): Mırıldanma / tek sesli enstrüman çalışını MIDI'ye çevirir.

Not: Bu ilk sürüm tek nota (monofonik) içindir — mırıldanma, tek telli/tek nota
gitar/flüt hattı gibi. Akorlu (polifonik) enstrüman çalışları için Basic Pitch
tabanlı ayrı bir modül (Faz 1 eklentisi, roadmap'te işaretli) sonra eklenecek.

Şu an notalar en yakın batı yarım tonuna (12-TET) yuvarlanıyor. Koma sesleri
(mikrotonal Türk müziği perdeleri) ve ayarlanabilir "ne kadar sıkı quantize"
seçeneği, pitch-bend tabanlı bir geliştirme olarak roadmap'te ayrı görev.
"""

import numpy as np
import librosa
import pretty_midi

MIN_NOTE_DURATION_SEC = 0.08


def _hz_to_midi_float(freq: float) -> float:
    return 69 + 12 * np.log2(freq / 440.0)


def transcribe_to_midi(wav_path: str, output_midi_path: str):
    """
    wav_path: mono WAV girdi dosyası
    output_midi_path: yazılacak .mid dosya yolu
    Dönüş: (output_midi_path, tespit_edilen_nota_sayisi)
    """
    y, sr = librosa.load(wav_path, sr=22050, mono=True)

    f0, voiced_flag, _voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )

    hop_length = 512
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    notes = []
    current = None

    for t, freq, voiced in zip(times, f0, voiced_flag):
        if voiced and freq and not np.isnan(freq):
            midi_nearest = int(round(_hz_to_midi_float(freq)))

            if current is None:
                current = {"start": t, "end": t, "pitch": midi_nearest}
            elif midi_nearest == current["pitch"]:
                current["end"] = t
            else:
                notes.append(current)
                current = {"start": t, "end": t, "pitch": midi_nearest}
        else:
            if current is not None:
                notes.append(current)
                current = None

    if current is not None:
        notes.append(current)

    # Çok kısa (gürültüden kaynaklı) notaları ele
    notes = [n for n in notes if (n["end"] - n["start"]) >= MIN_NOTE_DURATION_SEC]

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)  # yer tutucu ses (Acoustic Grand Piano)

    for n in notes:
        pitch = max(0, min(127, n["pitch"]))
        instrument.notes.append(
            pretty_midi.Note(
                velocity=90,
                pitch=pitch,
                start=n["start"],
                end=max(n["end"], n["start"] + 0.05),
            )
        )

    midi.instruments.append(instrument)
    midi.write(output_midi_path)

    return output_midi_path, len(notes)
