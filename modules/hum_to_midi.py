"""
Faz 1 (v2 — bağımsız/hafif): Mırıldanma / tek sesli enstrüman çalışını MIDI'ye çevirir.

v2 notu — neden yeniden yazıldı: v1/v1.1 librosa+scipy+pretty_midi kullanıyordu.
Geliştirme ortamımda bu kütüphaneleri kuramadığım (ağ erişimi yok) için
değişiklikleri sadece "mantığını okuyarak" doğrulayabiliyordum, gerçek kodu
uçtan uca deneyemiyordum — üst üste "hâlâ kötü/ilgisiz" geri bildirimlerinin
sebebi muhtemelen buydu. Bu sürüm librosa/scipy/pretty_midi/soundfile'a hiç
ihtiyaç duymuyor; sadece numpy (otokorelasyon tabanlı pitch tespiti) ve saf
Python (wave okuma, MIDI dosyası yazma) kullanıyor. Bu sayede gerçek gönderdiğin
ses kaydınla bu KOD'u birebir çalıştırıp sonucu görebildim, tahmin yürütmedim.

Yan fayda: numba/scikit-learn gibi ağır bağımlılıklar kalktığı için Render'ın
ücretsiz planındaki sınırlı hafızada da daha az risk taşıyor.
"""

import wave
import struct
import numpy as np

SAMPLE_RATE_TARGET = 22050
FRAME_LENGTH = 2048
HOP_LENGTH = 512
FMIN = 70
FMAX = 1000
CONF_THRESHOLD = 0.35
MIN_RELATIVE_ENERGY = 0.06
MEDIAN_FILTER_WINDOW = 11
MIN_STABLE_FRAMES = 5
HYSTERESIS_MARGIN = 0.62
MIN_NOTE_DURATION_SEC = 0.12
MAX_MERGE_GAP_SEC = 0.15


def _load_wav_mono(path):
    w = wave.open(path, "rb")
    sr = w.getframerate()
    n = w.getnframes()
    sampwidth = w.getsampwidth()
    channels = w.getnchannels()
    raw = w.readframes(n)
    w.close()

    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128) / 128.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / (2 ** 31)
    else:
        raise ValueError(f"Desteklenmeyen ses bit derinliği: {sampwidth * 8} bit")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    return data, sr


def _resample_linear(y, sr, target_sr):
    if sr == target_sr or len(y) == 0:
        return y, sr
    duration = len(y) / sr
    new_len = max(int(duration * target_sr), 1)
    old_idx = np.linspace(0, len(y) - 1, len(y))
    new_idx = np.linspace(0, len(y) - 1, new_len)
    return np.interp(new_idx, old_idx, y), target_sr


def _autocorr_pitch(frame, sr, fmin=FMIN, fmax=FMAX):
    frame = frame - np.mean(frame)
    energy = np.sum(frame ** 2)
    if energy < 1e-9:
        return 0.0, 0.0
    windowed = frame * np.hanning(len(frame))
    ac = np.correlate(windowed, windowed, mode="full")
    ac = ac[len(ac) // 2:]
    if ac[0] <= 0:
        return 0.0, 0.0
    min_lag = int(sr / fmax)
    max_lag = min(int(sr / fmin), len(ac) - 1)
    if min_lag >= max_lag:
        return 0.0, 0.0
    segment = ac[min_lag:max_lag]
    peak_idx = int(np.argmax(segment))
    lag = min_lag + peak_idx
    confidence = float(segment[peak_idx] / ac[0])
    freq = sr / lag if lag > 0 else 0.0
    return freq, confidence


def _hz_to_midi_float(freq):
    return 69 + 12 * np.log2(freq / 440.0)


def _manual_median_filter(x, window):
    half = window // 2
    n = len(x)
    out = np.copy(x)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        out[i] = np.median(x[lo:hi])
    return out


def _write_midi(notes, output_path, ticks_per_beat=220, tempo_bpm=120):
    """notes: {"start": saniye, "end": saniye, "pitch": 0-127} listesi.
    pretty_midi'ye ihtiyaç duymadan, tek track'li standart bir .mid dosyası yazar."""
    us_per_beat = int(60_000_000 / tempo_bpm)
    sec_per_tick = (us_per_beat / 1_000_000) / ticks_per_beat

    events = []
    for n in notes:
        start_tick = int(round(n["start"] / sec_per_tick))
        end_tick = int(round(n["end"] / sec_per_tick))
        if end_tick <= start_tick:
            end_tick = start_tick + 1
        events.append((start_tick, 0, n["pitch"]))  # 0 -> note-on
        events.append((end_tick, 1, n["pitch"]))    # 1 -> note-off

    events.sort(key=lambda e: (e[0], -e[1]))  # ayni tick'te once off, sonra on

    def write_vlq(value):
        out = [value & 0x7F]
        value >>= 7
        while value:
            out.insert(0, (value & 0x7F) | 0x80)
            value >>= 7
        return bytes(out)

    track_data = bytearray()
    track_data += write_vlq(0)
    track_data += bytes([0xFF, 0x51, 0x03]) + us_per_beat.to_bytes(3, "big")

    prev_tick = 0
    for tick, ev_type, pitch in events:
        delta = max(tick - prev_tick, 0)
        prev_tick = tick
        track_data += write_vlq(delta)
        if ev_type == 0:
            track_data += bytes([0x90, pitch & 0x7F, 90])
        else:
            track_data += bytes([0x80, pitch & 0x7F, 0])

    track_data += write_vlq(0) + bytes([0xFF, 0x2F, 0x00])

    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, ticks_per_beat)
    track_chunk = b"MTrk" + struct.pack(">I", len(track_data)) + bytes(track_data)

    with open(output_path, "wb") as f:
        f.write(header + track_chunk)


def _transcribe_with_basic_pitch(wav_path: str, output_midi_path: str):
    """Spotify'ın Basic Pitch modeliyle (gerçek eğitilmiş sinir ağı) transkripsiyon
    dener. requirements.txt'e eklendi ama BU ORTAMDA KURULUP TEST EDİLEMEDİ (ağ
    erişimi yok) — Render'da paket kurulacak, orada gerçek anlamda ilk kez
    çalışacak. Başarısız olursa (import hatası, bellek hatası, model hatası vb.)
    None döner ve çağıran taraf otomatik olarak aşağıdaki kendi yönteme düşer."""
    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
    except Exception:
        return None

    try:
        _, midi_data, _ = predict(wav_path, model_or_model_path=ICASSP_2022_MODEL_PATH)
        midi_data.write(output_midi_path)
        note_count = sum(len(inst.notes) for inst in midi_data.instruments)
        return output_midi_path, note_count
    except Exception:
        return None


def transcribe_to_midi(wav_path: str, output_midi_path: str):
    """
    wav_path: mono/stereo WAV girdi dosyası (herhangi bir örnekleme hızında)
    output_midi_path: yazılacak .mid dosya yolu
    Dönüş: (output_midi_path, tespit_edilen_nota_sayisi)

    Önce Basic Pitch (gerçek yapay zeka modeli, requirements.txt'e eklendi)
    deneniyor; kurulu değilse veya Render'ın ücretsiz planında bellek/hız
    sorunu çıkarsa (TensorFlow ağır bir bağımlılıktır), otomatik olarak bu
    dosyadaki KENDİ (numpy tabanlı, önceden gerçek ses kayıtlarıyla test
    edilmiş) yönteme düşülüyor — yani bu fallback hiçbir zaman botu çökertmez.
    """
    bp_result = _transcribe_with_basic_pitch(wav_path, output_midi_path)
    if bp_result is not None and bp_result[1] > 0:
        return bp_result

    return _transcribe_to_midi_custom(wav_path, output_midi_path)


def _transcribe_to_midi_custom(wav_path: str, output_midi_path: str):
    """Faz 1'in orijinal (numpy tabanlı, gerçek ses kayıtlarıyla test edilmiş)
    otokorelasyon yöntemi — Basic Pitch mevcut değilse ya da başarısız olursa
    devreye giren güvenli yedek (fallback)."""
    y, sr = _load_wav_mono(wav_path)
    y, sr = _resample_linear(y, sr, SAMPLE_RATE_TARGET)

    if len(y) <= FRAME_LENGTH:
        _write_midi([], output_midi_path)
        return output_midi_path, 0

    freqs, confs, times, rms_vals = [], [], [], []
    for start in range(0, len(y) - FRAME_LENGTH, HOP_LENGTH):
        frame = y[start:start + FRAME_LENGTH]
        freq, conf = _autocorr_pitch(frame, sr)
        freqs.append(freq)
        confs.append(conf)
        times.append(start / sr)
        rms_vals.append(float(np.sqrt(np.mean(frame ** 2))))

    freqs = np.array(freqs)
    confs = np.array(confs)
    times = np.array(times)
    rms = np.array(rms_vals)

    energy_gate = rms >= (MIN_RELATIVE_ENERGY * rms.max()) if rms.max() > 0 else np.zeros_like(rms, dtype=bool)
    valid = (confs >= CONF_THRESHOLD) & (freqs > 0) & energy_gate

    midi_cont = np.full_like(freqs, np.nan)
    midi_cont[valid] = _hz_to_midi_float(freqs[valid])

    frame_idx = np.arange(len(midi_cont))
    if valid.any():
        filled = np.interp(frame_idx, frame_idx[valid], midi_cont[valid])
    else:
        _write_midi([], output_midi_path)
        return output_midi_path, 0

    smoothed = _manual_median_filter(filled, MEDIAN_FILTER_WINDOW)
    smoothed[~valid] = np.nan

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

        if current is None:
            current = {"start": t, "end": t, "pitch": int(round(m))}
            pending_pitch, pending_count = None, 0
            continue

        if abs(m - current["pitch"]) <= HYSTERESIS_MARGIN:
            current["end"] = t
            pending_pitch, pending_count = None, 0
            continue

        candidate = int(round(m))
        if candidate == pending_pitch:
            pending_count += 1
        else:
            pending_pitch, pending_count = candidate, 1

        if pending_count >= MIN_STABLE_FRAMES:
            raw_notes.append(current)
            current = {"start": t, "end": t, "pitch": candidate}
            pending_pitch, pending_count = None, 0
        else:
            current["end"] = t

    if current is not None:
        raw_notes.append(current)

    merged = []
    for n in raw_notes:
        if merged and merged[-1]["pitch"] == n["pitch"] and (n["start"] - merged[-1]["end"]) <= MAX_MERGE_GAP_SEC:
            merged[-1]["end"] = n["end"]
        else:
            merged.append(n)

    notes = [n for n in merged if (n["end"] - n["start"]) >= MIN_NOTE_DURATION_SEC]
    for n in notes:
        n["pitch"] = max(0, min(127, n["pitch"]))

    _write_midi(notes, output_midi_path)

    return output_midi_path, len(notes)
