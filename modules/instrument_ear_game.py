"""
Ek: Enstrüman/tını tanıma oyunu. turkish_instruments.py'deki basit sentezleyiciyi
(ve birkaç GM-tarzı temel dalga formunu) kullanarak "bu hangi çalgı/tını"
tarzı bir kulak eğitimi oyunu. Dürüstlük notu: turkish_instruments.py'deki
"çalgı" tınıları gerçek örnek kayıt değil, basit additif sentez — yani bu oyun
gerçek çalgı tınısı ayırt etmeyi değil, temel dalga formu/harmonik karakter
farklarını ayırt etmeyi öğretir (basit ama yine de kulak eğitimi için faydalı).
"""

import random

from modules.turkish_instruments import INSTRUMENT_PROFILES, _synth_note, SAMPLE_RATE
import wave
import numpy as np


def _write_wav(samples, path, sr=SAMPLE_RATE):
    int16 = np.clip(samples * 32767, -32768, 32767).astype(np.int16)
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(int16.tobytes())
    w.close()


def make_timbre_question(output_wav_path, seed=None):
    rng = random.Random(seed)
    instruments = list(INSTRUMENT_PROFILES.keys())
    correct = rng.choice(instruments)
    profile = INSTRUMENT_PROFILES[correct]

    sig = _synth_note(293.66, 1.2, profile)  # D4 sabit notada, sadece tını değişir
    _write_wav(sig, output_wav_path)

    choices = list(instruments)
    rng.shuffle(choices)
    if correct not in choices[:4]:
        choices[3] = correct
    return {"correct_answer": correct, "choices": choices[:4]}
