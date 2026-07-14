"""
Ek: Referans şarkıdan pratik-along (minus-one) üretici.

Dürüstlük notu: Gerçek kaynak ayrıştırma (Demucs gibi eğitilmiş bir derin
öğrenme modeli) bu ortamda kurulamıyor (ağ erişimi yok). Burada "orta kanal
çıkarma" (center-channel subtraction) tekniği kullanılıyor: birçok stüdyo
kaydında lead vokal tam ortada (sol=sağ) karılır, sol-sağ kanalları
birbirinden çıkarınca ortadaki (genelde vokal) büyük ölçüde zayıflar. Bu basit
ve hızlı bir teknik ama Demucs kadar temiz değildir — davul/bas gibi ortada
karılmış diğer enstrümanları da hafifçe etkileyebilir, ve MONO kayıtlarda
hiç işe yaramaz (stereo şart).
"""

import wave
import numpy as np


def remove_center_channel(input_wav_path: str, output_wav_path: str):
    w = wave.open(input_wav_path, "rb")
    sr = w.getframerate()
    n = w.getnframes()
    sampwidth = w.getsampwidth()
    channels = w.getnchannels()
    raw = w.readframes(n)
    w.close()

    if channels != 2:
        raise ValueError("Bu teknik sadece stereo (2 kanallı) kayıtlarda çalışır.")
    if sampwidth != 2:
        raise ValueError("Sadece 16-bit WAV destekleniyor.")

    data = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    data = data.reshape(-1, 2)
    left, right = data[:, 0], data[:, 1]

    diff = (left - right) / 2.0
    out_stereo = np.stack([diff, diff], axis=1)

    out_int16 = np.clip(out_stereo * 32767, -32768, 32767).astype(np.int16)

    out_w = wave.open(output_wav_path, "wb")
    out_w.setnchannels(2)
    out_w.setsampwidth(2)
    out_w.setframerate(sr)
    out_w.writeframes(out_int16.tobytes())
    out_w.close()

    return output_wav_path
