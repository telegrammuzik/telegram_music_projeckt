"""
Faz 5: Solfej oyunları — aralık tanıma, nota tanıma, enstrüman/tını tanıma
oyunları. Sesleri basit sinüs-tabanlı bir sentezle üretiyoruz (gerçek çalgı
örnekleri değil, ama aralık/nota tanıma pratiği için frekans farkı yeterli).
Söylenen notanın doğruluğunu kontrol etmek için Faz 1'in pitch tespitini
(core.pitch) kullanıyoruz.
"""

import random
import wave
import numpy as np

from core.pitch import analyze_pitch_track, hz_to_note_and_cents
from core.wav_io import load_wav_mono

SAMPLE_RATE = 22050

INTERVALS = {
    "minör 2li": 1, "majör 2li": 2, "minör 3lü": 3, "majör 3lü": 4,
    "tam 4lü": 5, "tritone": 6, "tam 5li": 7, "minör 6lı": 8,
    "majör 6lı": 9, "minör 7li": 10, "majör 7li": 11, "oktav": 12,
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _sine_tone(freq, duration, sr=SAMPLE_RATE):
    n = int(duration * sr)
    t = np.linspace(0, duration, n, endpoint=False)
    envelope = np.ones(n)
    fade = int(0.02 * sr)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    return 0.4 * np.sin(2 * np.pi * freq * t) * envelope


def _write_wav(samples, path, sr=SAMPLE_RATE):
    int16 = np.clip(samples * 32767, -32768, 32767).astype(np.int16)
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(int16.tobytes())
    w.close()


def make_interval_question(output_wav_path, seed=None):
    rng = random.Random(seed)
    interval_name, semitones = rng.choice(list(INTERVALS.items()))
    root_midi = rng.randint(55, 67)
    root_freq = 440.0 * 2 ** ((root_midi - 69) / 12)
    second_freq = 440.0 * 2 ** ((root_midi + semitones - 69) / 12)

    tone1 = _sine_tone(root_freq, 0.6)
    silence = np.zeros(int(0.15 * SAMPLE_RATE))
    tone2 = _sine_tone(second_freq, 0.6)
    _write_wav(np.concatenate([tone1, silence, tone2]), output_wav_path)

    choices = list(INTERVALS.keys())
    rng.shuffle(choices)
    return {"correct_answer": interval_name, "choices": choices[:4] if interval_name in choices[:4] else choices[:3] + [interval_name]}


def make_note_id_question(output_wav_path, seed=None):
    rng = random.Random(seed)
    midi_note = rng.randint(60, 72)
    freq = 440.0 * 2 ** ((midi_note - 69) / 12)
    _write_wav(_sine_tone(freq, 1.0), output_wav_path)

    correct = NOTE_NAMES[midi_note % 12]
    choices = list(NOTE_NAMES)
    rng.shuffle(choices)
    if correct not in choices[:4]:
        choices[3] = correct
    return {"correct_answer": correct, "choices": choices[:4]}


def check_sung_note(wav_path, target_note_name):
    """Kullanıcının söylediği notanın hedef notaya (± yarım ton) yakınlığını kontrol eder."""
    y, sr = load_wav_mono(wav_path, target_sr=22050)
    times, freqs, confs = analyze_pitch_track(y, sr)
    valid = (confs > 0.4) & (freqs > 0)
    if not valid.any():
        return {"correct": False, "detail": "Net bir nota algılanamadı, tekrar dener misin?"}

    median_freq = float(np.median(freqs[valid]))
    name, midi_num, cents = hz_to_note_and_cents(median_freq)
    sung_pc = NOTE_NAMES[midi_num % 12]
    correct = sung_pc == target_note_name

    return {"correct": correct, "sung_note": name, "cents_off": cents,
            "detail": f"Söylediğin: {name} ({'doğru' if correct else 'hedef: ' + target_note_name})"}
