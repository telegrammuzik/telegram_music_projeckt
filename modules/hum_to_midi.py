"""
Faz 1 (v1 — monofonik): Mırıldanma / tek sesli enstrüman çalışını MIDI'ye çevirir.

Not: Bu ilk sürüm tek nota (monofonik) içindir — mırıldanma, tek telli/tek nota
gitar/flüt hattı gibi. Akorlu (polifonik) enstrüman çalışları için Basic Pitch
tabanlı ayrı bir modül (Faz 1 eklentisi, roadmap'te işaretli) sonra eklenecek.

Şu an notalar en yakın batı yarım tonuna (12-TET) yuvarlanıyor. Koma sesleri
(mikrotonal Türk müziği perdeleri) ve ayarlanabilir "ne kadar sıkı quantize"
seçeneği, pitch-bend tabanlı bir geliştirme olarak roadmap'te ayrı görev.

v1.1 güncellemesi: ilk sürümde mırıldanmadaki doğal titreşim/vibrato ve pyin'in
kare kare ufak dalgalanmaları, tek bir uzun notayı onlarca kırık mikro-notaya
bölüyordu ("kötü çeviri" şikayetinin sebebi). Bunu düzeltmek için:
  1. Ham pitch eğrisi medyan filtreyle yumuşatılıyor (tekil karesel sıçramalar elenir)
  2. Nota değişimi artık "histerezis" ile karar veriliyor: yeni perde en az
     birkaç ardışık karede kararlı kalmadan nota değişmiyor
  3. Aynı perdeye sahip, aralarında çok kısa (nefes/algı boşluğu kaynaklı)
     boşluk olan notalar birleştiriliyor
  4. Düşük güvenilirlikli (voiced_prob düşük) kareler pitch hesaplamasına dahil edilmiyor
"""

import numpy as np
import librosa
import pretty_midi
from scipy.signal import medfilt

MIN_NOTE_DURATION_SEC = 0.09
MIN_STABLE_FRAMES = 3          # yeni perdenin nota değişimi için kararlı kalması gereken kare sayısı
MAX_MERGE_GAP_SEC = 0.12       # aynı perdeye sahip notalar arasında birleştirilecek maksimum boşluk
VOICED_PROB_THRESHOLD = 0.5    # bu değerin altındaki kareler güvenilmez sayılıp atlanır
MEDIAN_FILTER_WINDOW = 7       # ham pitch eğrisini yumuşatmak için (kare sayısı, tek sayı olmalı)


def _hz_to_midi_float(freq: float) -> float:
    return 69 + 12 * np.log2(freq / 440.0)


def transcribe_to_midi(wav_path: str, output_midi_path: str):
    """
    wav_path: mono WAV girdi dosyası
    output_midi_path: yazılacak .mid dosya yolu
    Dönüş: (output_midi_path, tespit_edilen_nota_sayisi)
    """
    y, sr = librosa.load(wav_path, sr=22050, mono=True)

    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )

    hop_length = 512
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    # 1) Güvenilir olmayan kareleri (düşük voiced_prob) sessiz say
    valid = voiced_flag & (voiced_prob >= VOICED_PROB_THRESHOLD) & ~np.isnan(f0)

    # 2) Ham frekansı sürekli (float) MIDI nota numarasına çevir
    midi_continuous = np.full_like(f0, np.nan, dtype=float)
    midi_continuous[valid] = _hz_to_midi_float(f0[valid])

    # 3) Medyan filtreyle yumuşat (sadece geçerli bölgeler üstünde, kısa boşlukları
    # etkilemeden) — tekil karesel sıçramaları eler, gerçek nota değişimlerini korur.
    # Boşlukları 0 ile doldurmak yerine ara değer (interpolasyon) kullanıyoruz,
    # yoksa medyan filtre boşluk kenarlarındaki gerçek notaları "0 perdesine"
    # doğru çekip nota başı/sonunda hatalı kısa notalara yol açabiliyordu.
    frame_idx = np.arange(len(midi_continuous))
    if valid.any():
        filled = np.interp(frame_idx, frame_idx[valid], midi_continuous[valid])
    else:
        filled = np.zeros_like(midi_continuous)
    smoothed = medfilt(filled, kernel_size=MEDIAN_FILTER_WINDOW)
    smoothed[~valid] = np.nan

    # 4) Histerezisli nota segmentasyonu: yeni perde en az MIN_STABLE_FRAMES kare
    # boyunca kararlı kalmadan nota değişmesin (vibrato/titreşim yüzünden gereksiz
    # mikro-nota bölünmesini engeller)
    raw_notes = []
    current = None
    pending_pitch = None
    pending_count = 0

    for t, m in zip(times, smoothed):
        if np.isnan(m):
            if current is not None:
                raw_notes.append(current)
                current = None
            pending_pitch, pending_count = None, 0
            continue

        candidate = int(round(m))

        if current is None:
            current = {"start": t, "end": t, "pitch": candidate, "raw": [m]}
            pending_pitch, pending_count = None, 0
            continue

        if candidate == current["pitch"]:
            current["end"] = t
            current["raw"].append(m)
            pending_pitch, pending_count = None, 0
        else:
            if candidate == pending_pitch:
                pending_count += 1
            else:
                pending_pitch, pending_count = candidate, 1

            if pending_count >= MIN_STABLE_FRAMES:
                # Yeni perde yeterince kararlı kaldı, gerçek bir nota değişimi kabul et
                raw_notes.append(current)
                current = {"start": t, "end": t, "pitch": candidate, "raw": [m]}
                pending_pitch, pending_count = None, 0
            else:
                # Geçici/gürültü sayılan sapma — mevcut notaya devam et
                current["end"] = t

    if current is not None:
        raw_notes.append(current)

    # 5) Aynı perdeye sahip, çok kısa boşlukla ayrılmış ardışık notaları birleştir
    merged = []
    for n in raw_notes:
        if merged and merged[-1]["pitch"] == n["pitch"] and (n["start"] - merged[-1]["end"]) <= MAX_MERGE_GAP_SEC:
            merged[-1]["end"] = n["end"]
            merged[-1]["raw"].extend(n["raw"])
        else:
            merged.append(n)

    # 6) Çok kısa (gürültüden kaynaklı) notaları ele
    notes = [n for n in merged if (n["end"] - n["start"]) >= MIN_NOTE_DURATION_SEC]

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
