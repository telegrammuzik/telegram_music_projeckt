"""
Ortak ses işleme katmanı (Faz 0). Tüm ses tabanlı modüller (mırıldanma->MIDI,
akor tespiti, mix/mastering analizi, tuner vb.) ses dosyası indirme/dönüştürme
işini burada paylaşır — her modül kendi ffmpeg kodunu yazmaz.
"""

import subprocess
import tempfile


def convert_to_wav(input_path: str, sample_rate: int = 22050) -> str:
    """Herhangi bir ses formatını (ogg/opus/mp3/m4a vb.) mono WAV'a çevirir."""
    output_path = tempfile.mktemp(suffix=".wav")
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ac", "1", "-ar", str(sample_rate),
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg dönüştürme hatası: {result.stderr.decode(errors='ignore')}"
        )
    return output_path
