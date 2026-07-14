"""
Faz 6: Nota okuma eğitimi. Gerçek porte görseli üretmek için (music21/LilyPond)
network erişimi gerekiyor; bu ortamda kuramadım. Bunun yerine basit bir metin
tabanlı porte gösterimi (nota adı + porte üzerindeki konumu ASCII ile) ve
buton tabanlı quizler kullanıyoruz — görsel değil ama işlevsel bir başlangıç.
İleride gerçek porte görseli (matplotlib veya benzeri, deploy ortamında
kurulabilirse) eklenebilir.
"""

import random

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Sol anahtarında (treble clef), porte çizgileri ve aralarındaki notalar
# (E4 alt çizgiden B5 üst çizgiye kadar, basitleştirilmiş)
TREBLE_POSITIONS = {
    "E4": "en alt çizgi", "F4": "1. aralık", "G4": "2. çizgi", "A4": "2. aralık",
    "B4": "3. çizgi (orta)", "C5": "3. aralık", "D5": "4. çizgi", "E5": "4. aralık", "F5": "en üst çizgi",
}

LESSONS = [
    {
        "title": "Porte ve Anahtarlar",
        "text": (
            "Porte (staff), 5 çizgi ve 4 aralıktan oluşur. Sol anahtarı (treble clef) "
            "genelde daha tiz sesli enstrümanlar/sağ el piyano için, fa anahtarı (bass clef) "
            "daha pes sesler/sol el piyano için kullanılır."
        ),
    },
    {
        "title": "Sol Anahtarında Notalar",
        "text": (
            "Çizgiler (alttan üste): E-G-B-D-F ('Every Good Boy Does Fine' gibi ezberleme cümleleri kullanılır). "
            "Aralıklar (alttan üste): F-A-C-E (kelime gibi: FACE)."
        ),
    },
    {
        "title": "Ritim Değerleri",
        "text": (
            "Tam nota (4 vuruş), yarım nota (2 vuruş), dörtlük nota (1 vuruş), sekizlik nota (yarım vuruş). "
            "Bir dörtlük notaya bağlı nokta, süresinin yarısı kadar ekler."
        ),
    },
]

QUIZ_POOL = list(TREBLE_POSITIONS.items())


def get_lesson(index: int):
    if index < 0 or index >= len(LESSONS):
        return None
    return LESSONS[index]


def make_note_position_question(seed=None):
    rng = random.Random(seed)
    note_name, position = rng.choice(QUIZ_POOL)
    choices = [p for _, p in QUIZ_POOL]
    rng.shuffle(choices)
    choices = list(dict.fromkeys(choices))[:4]
    if position not in choices:
        choices[0] = position
    return {"question": f"{note_name} notası sol anahtarında nerede?", "correct_answer": position, "choices": choices}
