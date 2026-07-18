"""
Ek: Kayıt öncesi ortam/mikrofon kontrolü. Mırıldanma kaydından önce (ya da
hemen sonra, gönderilen kayıt üzerinde) gürültü/sinyal oranını kabaca ölçüp
kullanıcıyı uyarır. Gerçek bir "gürültü profili" analizden çok, basit bir
enerji/tutarlılık kontrolüdür.
"""

import numpy as np

from core.wav_io import load_wav_mono
from core.pitch import analyze_pitch_track


def check_recording_quality(wav_path: str):
    y, sr = load_wav_mono(wav_path, target_sr=22050)

    if len(y) < sr * 0.3:
        return {"ok": False, "message": "Kayıt çok kısa (0.3 saniyeden az). Biraz daha uzun bir kayıt gönder."}

    rms = np.sqrt(np.mean(y ** 2))
    peak = np.max(np.abs(y))

    if peak < 0.02:
        return {"ok": False, "message": "Ses çok kısık geldi — mikrofona biraz daha yaklaşıp tekrar dener misin?"}

    times, freqs, confs = analyze_pitch_track(y, sr)
    voiced_ratio = float(np.mean(confs > 0.4)) if len(confs) else 0.0

    if voiced_ratio < 0.15:
        return {
            "ok": False,
            "message": "Kayıtta net bir ses/nota oranı düşük — arka planda gürültü olabilir ya da mırıldanma çok kısık kalmış. Sessiz bir ortamda, mikrofona yakın tekrar dener misin?",
        }

    crest = peak / max(rms, 1e-9)
    if crest > 20:
        return {
            "ok": True,
            "message": "Kayıt kullanılabilir görünüyor, ama ani gürültü darbeleri (ör. mikrofon vuruşu) tespit edildi.",
        }

    return {"ok": True, "message": "Kayıt kalitesi iyi görünüyor."}
