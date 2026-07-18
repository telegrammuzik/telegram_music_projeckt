"""
Ek: Enstrüman/tını tanıma oyunu. turkish_instruments.py'deki (v2, araştırmaya
dayalı fiziksel modelleme kullanan) sentezleyicileri kullanarak "bu hangi
çalgı" tarzı bir kulak eğitimi oyunu. Dürüstlük notu: bu tınılar gerçek örnek
kayıt değil, sentezdir — ama artık her çalgının gerçek akustik özelliklerine
(kamış tipi, drone/detune, yay/nefes gürültüsü vb.) göre ayrı ayrı modellendiği
için birbirinden çok daha net ayırt edilebilir olmalı.
"""

import random
import wave
import numpy as np

from modules.turkish_instruments import INSTRUMENT_SYNTHS, SAMPLE_RATE


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
    instruments = list(INSTRUMENT_SYNTHS.keys())
    correct = rng.choice(instruments)
    synth_fn = INSTRUMENT_SYNTHS[correct]

    sig = synth_fn(293.66, 1.2, SAMPLE_RATE, None)  # D4 sabit notada, sadece tını değişir
    _write_wav(sig, output_wav_path)

    choices = list(instruments)
    rng.shuffle(choices)
    if correct not in choices[:4]:
        choices[3] = correct
    return {"correct_answer": correct, "choices": choices[:4]}
