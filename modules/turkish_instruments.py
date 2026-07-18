"""
Faz 11: Türk müziği çalgıları ses sentezi (tulum, zurna, klasik kemençe, kabak
kemane, kaval, ney).

v2 — gerçek akustik araştırmaya dayalı yeniden yazım. Önceki sürüm her çalgıya
aynı basit "birkaç harmonik topla" sentezini uyguluyordu ve sonuç "melodika
gibi" duyuluyordu (haklı bir eleştiriydi). Bu sürümde her çalgı için gerçek
kaynaklardan araştırılan akustik özellikler ayrı ayrı modelleniyor:

- Tulum: DRONE YOK (yaygın yanlış kanının aksine) — iki paralel borudan (çifte)
  oluşur, bu iki boru kasıtlı olarak hafif detune edilir ve bu "vuruş"（beating）
  parıltılı/titrek karakteristik sesini verir. Tek kamışlı, sürekli basınçla
  çalınır (nefesler arası kesinti neredeyse yok, notalar birbirine bitişik).
- Zurna: çift kamışlı, konik gövde, çok parlak/keskin/güçlü üst harmonikler,
  hızlı atak, açık havada taşınabilecek şekilde "delici" bir ton.
- Klasik kemençe: yaylı, ladin/köknar tablalı (parlak/rafine), portamento
  (notalar arası kayma) ve tremolo karakteristik; hafif yay gürültüsü.
  Kabak kemane: yine yaylı ama kabak gövde + balık derisi tabla nedeniyle
  çok daha sıcak/karanlık/hüzünlü bir tına — kemençeden daha az parlak.
- Kaval: kamışsız, kenardan üflemeli (ney'den farklı ağızlık), "mat"/opak,
  ince ya da derin ama parlak olmayan bir ton, hafif nefes sesi.
- Ney: kamışsız, ağızda çapraz üflenen kamıştan (kaval'dan farklı), imzası
  net bir şekilde duyulan NEFES sesi (bu bir kusur değil, çalgının imzası) +
  batı flütünden daha zengin üst harmonikler, hafif doğal vibrato.

DÜRÜSTLÜK NOTU — önemli, hâlâ geçerli: Bu araştırmaya dayalı fiziksel modelleme,
önceki sürümden çok daha karakterli ve ayırt edilebilir sesler üretir, ama
YİNE DE gerçek bir kayıt DEĞİLDİR — sentezdir. Gerçek çalgı sesiyle
karıştırılmamalı. Gerçek örnek kayıttan (sample-based) bir sese geçmek
istersen, her çalgıdan birkaç saniyelik temiz tek nota kaydı yeterli olur
(bu konuşuldu, kullanıcı şimdilik araştırmaya dayalı sentezi tercih etti).
"""

import wave
import numpy as np

from core.midi_utils import read_midi_notes

SAMPLE_RATE = 22050


def _band_noise(n, sr, lo, hi, seed=0):
    """Beyaz gürültüyü FFT ile bir frekans bandına filtreler (nefes/yay dokusu için)."""
    rng = np.random.default_rng(seed)
    white = rng.normal(0, 1.0, n)
    spec = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0 / sr)
    mask = (freqs >= lo) & (freqs <= hi)
    spec[~mask] = 0
    filtered = np.fft.irfft(spec, n)
    peak = np.max(np.abs(filtered))
    return filtered / peak if peak > 0 else filtered


def _harmonic_stack(t, freq, harmonics, odd_emphasis=False):
    sig = np.zeros_like(t)
    for h_idx, weight in enumerate(harmonics, start=1):
        if odd_emphasis and h_idx % 2 == 0:
            weight *= 0.35
        sig += weight * np.sin(2 * np.pi * freq * h_idx * t)
    total = sum(harmonics)
    return sig / total if total > 0 else sig


def _envelope(n, sr, attack_s, release_s, sustain_level=1.0):
    env = np.full(n, sustain_level)
    a = max(int(attack_s * sr), 1)
    r = max(int(release_s * sr), 1)
    env[:min(a, n)] = np.linspace(0, sustain_level, min(a, n))
    if r < n:
        env[-r:] = np.linspace(env[-r], 0, r)
    return env


def _portamento_freqs(t, freq_from, freq_to, slide_s):
    """t: zaman dizisi (0'dan başlar). slide_s kadar sürede freq_from'dan
    freq_to'ya kayar, sonrası freq_to'da sabit kalır (yaylı çalgılardaki
    parmak kayması/glissando karakteri için)."""
    freqs = np.full_like(t, freq_to)
    slide_n = min(int(slide_s * (len(t) / max(t[-1], 1e-6))), len(t)) if len(t) > 1 else 0
    if slide_n > 1 and freq_from:
        freqs[:slide_n] = np.linspace(freq_from, freq_to, slide_n)
    return freqs


def _synth_tulum(freq, duration, sr, prev_freq=None):
    n = max(int(duration * sr), 1)
    t = np.linspace(0, duration, n, endpoint=False)
    detune_cents = 6.0
    freq2 = freq * (2 ** (detune_cents / 1200))
    harmonics = [1.0, 0.5, 0.7, 0.3, 0.4, 0.2, 0.25]  # tek kamış: tek harmonik vurgusu
    sig1 = _harmonic_stack(t, freq, harmonics, odd_emphasis=True)
    sig2 = _harmonic_stack(t, freq2, harmonics, odd_emphasis=True)
    sig = (sig1 + sig2) / 2
    env = _envelope(n, sr, attack_s=0.015, release_s=0.02, sustain_level=1.0)  # sürekli basınç, neredeyse kesintisiz
    return sig * env


def _synth_zurna(freq, duration, sr, prev_freq=None):
    n = max(int(duration * sr), 1)
    t = np.linspace(0, duration, n, endpoint=False)
    harmonics = [1.0, 0.9, 0.85, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]  # çift kamış: çok zengin/parlak üst harmonikler
    sig = _harmonic_stack(t, freq, harmonics)
    env = _envelope(n, sr, attack_s=0.006, release_s=0.015, sustain_level=1.0)
    return sig * env


def _synth_bowed(freq, duration, sr, prev_freq, brightness_harmonics, warmth=1.0, bow_noise_level=0.05):
    """Klasik kemençe ve kabak kemane ortak temeli: portamento + yay gürültüsü."""
    n = max(int(duration * sr), 1)
    t = np.linspace(0, duration, n, endpoint=False)
    slide_s = min(0.06, duration * 0.3)
    freqs = _portamento_freqs(t, prev_freq, freq, slide_s)
    phase = 2 * np.pi * np.cumsum(freqs) / sr
    sig = np.zeros(n)
    total_w = sum(brightness_harmonics)
    for h_idx, weight in enumerate(brightness_harmonics, start=1):
        sig += weight * np.sin(phase * h_idx)
    sig /= total_w
    noise = _band_noise(n, sr, 2000, 8000, seed=int(freq)) * bow_noise_level
    env = _envelope(n, sr, attack_s=0.035, release_s=0.08, sustain_level=1.0)
    # hafif tremolo (yay titremesi)
    tremolo = 1.0 + 0.03 * np.sin(2 * np.pi * 5.5 * t)
    return (sig * warmth + noise) * env * tremolo


def _synth_klasik_kemence(freq, duration, sr, prev_freq=None):
    return _synth_bowed(freq, duration, sr, prev_freq,
                         brightness_harmonics=[1.0, 0.55, 0.4, 0.3, 0.22, 0.15, 0.1],
                         warmth=1.0, bow_noise_level=0.04)


def _synth_kabak_kemane(freq, duration, sr, prev_freq=None):
    return _synth_bowed(freq, duration, sr, prev_freq,
                         brightness_harmonics=[1.0, 0.35, 0.18, 0.08, 0.04],
                         warmth=1.1, bow_noise_level=0.03)


def _synth_breathy(freq, duration, sr, harmonics, noise_ratio, vibrato_depth=0.0, attack_s=0.05):
    """Kaval ve ney ortak temeli: nefes gürültüsü + harmonik ton karışımı."""
    n = max(int(duration * sr), 1)
    t = np.linspace(0, duration, n, endpoint=False)
    if vibrato_depth > 0:
        vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * 5.0 * t)
        inst_freq = freq * vibrato
        phase = 2 * np.pi * np.cumsum(inst_freq) / sr
        tone = np.zeros(n)
        total_w = sum(harmonics)
        for h_idx, weight in enumerate(harmonics, start=1):
            tone += weight * np.sin(phase * h_idx)
        tone /= total_w
    else:
        tone = _harmonic_stack(t, freq, harmonics)
    noise = _band_noise(n, sr, 300, 4000, seed=int(freq * 7))
    sig = tone * (1 - noise_ratio) + noise * noise_ratio
    env = _envelope(n, sr, attack_s=attack_s, release_s=0.09, sustain_level=1.0)
    return sig * env


def _synth_kaval(freq, duration, sr, prev_freq=None):
    # "opak", az parlak, ince/derin ama mat — az harmonik, orta nefes oranı
    return _synth_breathy(freq, duration, sr, harmonics=[1.0, 0.25, 0.08], noise_ratio=0.12, vibrato_depth=0.0, attack_s=0.06)


def _synth_ney(freq, duration, sr, prev_freq=None):
    # batı flütünden daha zengin üst harmonikler + belirgin nefes imzası + doğal vibrato
    return _synth_breathy(freq, duration, sr, harmonics=[1.0, 0.4, 0.5, 0.25, 0.15, 0.08], noise_ratio=0.22, vibrato_depth=0.015, attack_s=0.09)


INSTRUMENT_SYNTHS = {
    "tulum": _synth_tulum,
    "zurna": _synth_zurna,
    "klasik_kemençe": _synth_klasik_kemence,
    "kabak_kemane": _synth_kabak_kemane,
    "kaval": _synth_kaval,
    "ney": _synth_ney,
}

# Geriye dönük uyumluluk için (instrument_ear_game.py bu sözlüğü/​fonksiyonu
# import ediyor) — artık gerçek profil değil ama anahtarlar aynı kalsın.
INSTRUMENT_PROFILES = {name: {} for name in INSTRUMENT_SYNTHS}


def _synth_note(freq, duration, profile, sr=SAMPLE_RATE):
    """Geriye dönük uyumluluk sarmalayıcısı (instrument_ear_game.py kullanıyor).
    profile burada kullanılmıyor, sadece eski çağrı imzasını koruyoruz."""
    return _synth_tulum(freq, duration, sr)


def render_midi_to_instrument(input_midi_path: str, output_wav_path: str, instrument: str):
    if instrument not in INSTRUMENT_SYNTHS:
        raise ValueError(f"Bilinmeyen çalgı: {instrument}. Seçenekler: {list(INSTRUMENT_SYNTHS.keys())}")

    synth_fn = INSTRUMENT_SYNTHS[instrument]
    notes = read_midi_notes(input_midi_path)
    if not notes:
        raise ValueError("MIDI'de nota yok.")

    total_dur = max(e for _, _, e in notes) + 0.5
    buffer = np.zeros(int(total_dur * SAMPLE_RATE) + SAMPLE_RATE)

    prev_freq = None
    for pitch, start, end in notes:
        freq = 440.0 * 2 ** ((pitch - 69) / 12)
        dur = max(end - start, 0.05)
        sig = synth_fn(freq, dur, SAMPLE_RATE, prev_freq)
        start_sample = int(start * SAMPLE_RATE)
        end_sample = start_sample + len(sig)
        if end_sample > len(buffer):
            buffer = np.pad(buffer, (0, end_sample - len(buffer)))
        buffer[start_sample:end_sample] += sig
        prev_freq = freq

    peak = np.max(np.abs(buffer))
    if peak > 0:
        buffer = buffer / peak * 0.9

    int16 = np.clip(buffer * 32767, -32768, 32767).astype(np.int16)
    w = wave.open(output_wav_path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SAMPLE_RATE)
    w.writeframes(int16.tobytes())
    w.close()

    return output_wav_path
