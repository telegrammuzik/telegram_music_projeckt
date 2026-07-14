"""
Faz 10: Mix & Mastering asistanı. Yüklenen bir ses dosyasını analiz edip
(frekans dengesi, yaklaşık loudness, dinamik aralık, stereo genişlik, clipping)
somut öneriler verir.

Dürüstlük notu: Bu bir ANALİZ + ÖNERİ asistanıdır — LANDR/iZotope Ozone gibi
ücretli, özel eğitilmiş modellerle çalışan tam otomatik mastering araçlarının
kalitesini iddia etmiyor. Loudness ölçümü de tam ITU-R BS.1770 (gerçek LUFS)
standardı değil, basitleştirilmiş bir RMS-tabanlı yaklaşık değer.
"""

import wave
import numpy as np


def _load_wav_stereo_or_mono(path):
    w = wave.open(path, "rb")
    sr = w.getframerate()
    n = w.getnframes()
    sampwidth = w.getsampwidth()
    channels = w.getnchannels()
    raw = w.readframes(n)
    w.close()

    if sampwidth != 2:
        raise ValueError("Bu analiz şu an sadece 16-bit WAV destekliyor.")

    data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    if channels == 2:
        data = data.reshape(-1, 2)
    else:
        data = data.reshape(-1, 1)
    return data, sr, channels


def analyze_mix(wav_path: str):
    data, sr, channels = _load_wav_stereo_or_mono(wav_path)
    mono = data.mean(axis=1)

    # 1) Yaklaşık loudness (RMS tabanlı, dBFS)
    rms = np.sqrt(np.mean(mono ** 2))
    rms_db = 20 * np.log10(max(rms, 1e-9))

    # 2) Clipping tespiti
    clip_threshold = 0.99
    clipped_ratio = float(np.mean(np.abs(mono) >= clip_threshold))

    # 3) Dinamik aralık (kaba): RMS'in tepe (peak) değerine oranı
    peak = float(np.max(np.abs(mono)))
    crest_factor_db = 20 * np.log10(max(peak, 1e-9) / max(rms, 1e-9))

    # 4) Frekans dengesi: FFT ile bas/orta/tiz enerji oranı
    window = np.hanning(len(mono)) if len(mono) < 500000 else np.hanning(500000)
    seg = mono[:len(window)]
    spec = np.abs(np.fft.rfft(seg * window))
    freqs = np.fft.rfftfreq(len(seg), d=1.0 / sr)

    def band_energy(lo, hi):
        mask = (freqs >= lo) & (freqs < hi)
        return float(np.sum(spec[mask] ** 2))

    bass_e = band_energy(20, 250)
    mid_e = band_energy(250, 4000)
    high_e = band_energy(4000, 16000)
    total_e = max(bass_e + mid_e + high_e, 1e-9)
    bass_pct = 100 * bass_e / total_e
    mid_pct = 100 * mid_e / total_e
    high_pct = 100 * high_e / total_e

    # 5) Stereo genişlik (varsa)
    stereo_corr = None
    if channels == 2:
        left, right = data[:, 0], data[:, 1]
        if np.std(left) > 0 and np.std(right) > 0:
            stereo_corr = float(np.corrcoef(left, right)[0, 1])

    suggestions = []
    if rms_db > -8:
        suggestions.append(f"Loudness yaklaşık {rms_db:.1f} dBFS (RMS) — oldukça yüksek, aşırı sıkıştırılmış (over-compressed) olabilir. Streaming platformları genelde -14 LUFS civarını hedefler, bu kabaca -14 ile -10 dBFS RMS bandına denk gelir.")
    elif rms_db < -20:
        suggestions.append(f"Loudness yaklaşık {rms_db:.1f} dBFS (RMS) — oldukça düşük, mastering aşamasında biraz daha yükseltilebilir.")
    else:
        suggestions.append(f"Loudness yaklaşık {rms_db:.1f} dBFS (RMS) — makul bir aralıkta.")

    if clipped_ratio > 0.001:
        suggestions.append(f"Kayıtta clipping (kırpılma) tespit edildi (~%{clipped_ratio*100:.2f} örnek). Limiter/gain ayarını gözden geçir.")

    if crest_factor_db < 6:
        suggestions.append("Dinamik aralık dar (crest factor düşük) — aşırı sıkıştırma/limiting olabilir, biraz nefes alanı bırakmayı düşün.")

    if bass_pct > 45:
        suggestions.append(f"Bas frekanslarda (20-250Hz) enerji fazla (~%{bass_pct:.0f}) — bir miktar düşürmeyi (high-pass/EQ) düşünebilirsin.")
    if high_pct < 10:
        suggestions.append(f"Tiz frekanslarda (4-16kHz) enerji az (~%{high_pct:.0f}) — mix biraz mat/karanlık gelebilir, biraz parlaklık eklemeyi düşün.")
    if high_pct > 35:
        suggestions.append(f"Tiz frekanslarda enerji fazla (~%{high_pct:.0f}) — sert/keskin gelebilir.")

    if stereo_corr is not None:
        if stereo_corr > 0.98:
            suggestions.append("Stereo genişlik çok dar (sol/sağ neredeyse mono gibi) — geniş bir hisse ihtiyaç varsa stereo genişletme düşünülebilir.")
        elif stereo_corr < 0.3:
            suggestions.append("Stereo genişlik çok fazla, faz sorunları (mono uyumluluk kaybı) olabilir — mono'da dinleyip kontrol et.")

    return {
        "loudness_dbfs_rms": rms_db,
        "peak": peak,
        "crest_factor_db": crest_factor_db,
        "clipped_ratio": clipped_ratio,
        "freq_balance": {"bass_pct": bass_pct, "mid_pct": mid_pct, "high_pct": high_pct},
        "stereo_correlation": stereo_corr,
        "suggestions": suggestions,
    }


def compare_with_reference(wav_path: str, reference_wav_path: str):
    """Faz 10 eklentisi: kendi mix'ini bir referans kayıtla karşılaştırır."""
    mine = analyze_mix(wav_path)
    ref = analyze_mix(reference_wav_path)

    diff_loudness = mine["loudness_dbfs_rms"] - ref["loudness_dbfs_rms"]
    diff_bass = mine["freq_balance"]["bass_pct"] - ref["freq_balance"]["bass_pct"]
    diff_high = mine["freq_balance"]["high_pct"] - ref["freq_balance"]["high_pct"]

    notes = []
    if abs(diff_loudness) > 3:
        notes.append(f"Loudness referanstan {abs(diff_loudness):.1f} dB {'yüksek' if diff_loudness>0 else 'düşük'}.")
    if abs(diff_bass) > 8:
        notes.append(f"Bas enerjisi referanstan %{abs(diff_bass):.0f} {'fazla' if diff_bass>0 else 'az'}.")
    if abs(diff_high) > 8:
        notes.append(f"Tiz enerjisi referanstan %{abs(diff_high):.0f} {'fazla' if diff_high>0 else 'az'}.")
    if not notes:
        notes.append("Genel denge referansa oldukça yakın.")

    return {"mine": mine, "reference": ref, "notes": notes}
