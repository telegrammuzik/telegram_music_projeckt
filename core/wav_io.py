"""Ortak WAV okuma (Faz 0). Birden fazla modül (hum_to_midi, chords, mix_master,
tuner, vocal_range) aynı WAV yükleme mantığına ihtiyaç duyuyor."""

import wave
import numpy as np


def load_wav_mono(path, target_sr=None):
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

    if target_sr and target_sr != sr:
        duration = len(data) / sr
        new_len = max(int(duration * target_sr), 1)
        old_idx = np.linspace(0, len(data) - 1, len(data))
        new_idx = np.linspace(0, len(data) - 1, new_len)
        data = np.interp(new_idx, old_idx, data)
        sr = target_sr

    return data, sr
