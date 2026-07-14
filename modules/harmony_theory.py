"""
Faz 7: Armoni eğitimi — Batı armonisi (olgun/rule-based zemin) ve Doğu/Makam
armonisi (deneysel, tanıtım niteliğinde içerik + koma sesi hesaplama).
"""

import random

from core.music_theory import NOTE_NAMES, diatonic_chords, ROMAN

WESTERN_LESSONS = [
    {
        "title": "Akor Fonksiyonları",
        "text": (
            "Bir tonun 7 diyatonik akoru üç ana fonksiyona ayrılır: Tonik (I, VI, III — "
            "dinlenme/huzur hissi), Subdominant (IV, II — hareket/geçiş), Dominant (V, VII — "
            "gerilim, tonike dönme isteği yaratır)."
        ),
    },
    {
        "title": "Kadanslar",
        "text": (
            "Otantik kadans (V-I): en güçlü 'bitmiş' hissi. Plagal kadans (IV-I): 'amin kadansı', "
            "daha yumuşak. Yarım kadans (I-V veya II-V): cümle ortasında gibi hissettirir, bitmemiş. "
            "Aldatıcı kadans (V-VI): beklenen I yerine VI'ya gider, şaşırtır."
        ),
    },
    {
        "title": "Ses Yürüyüşü (Voice Leading)",
        "text": (
            "Akorlar arası geçişte sesler mümkün olduğunca az hareket etmeli (ortak notalar tutulur, "
            "diğerleri en yakın komşu nota ile ilerler). Ardışık paralel 5'li ve 8'liden kaçınılır "
            "(klasik armonide 'yasak' sayılır, boş/ilkel bir ses verdiği düşünülür)."
        ),
    },
]

MAKAM_INTRO = (
    "Türk makam müziği, batı armonisinden temelde farklı bir sistemdir: 12 eşit "
    "yarım ton yerine, oktavı 53 'koma'ya bölen (Arel-Ezgi-Uzdilek/AEU sistemi) "
    "mikrotonal bir perde yapısı kullanır. Örneğin 'bakiye diyez' (~90 cent), "
    "batı diyezinden (100 cent) farklıdır; 'koma diyez' sadece ~22.6 cent'lik "
    "küçük bir kayma yapar. Bu yüzden makam müziğinde 'armoni' kavramı batı "
    "anlamında akor ilerlemesinden çok, makamın kendi seyir (melodik "
    "gelişim) kurallarına dayanır. Bu bölüm henüz deneysel — kulağınla "
    "birlikte geliştireceğiz."
)

COMMA_ACCIDENTALS = {
    "koma diyez": 22.6, "koma bemol": -22.6,
    "bakiye diyez": 90.6, "bakiye bemol": -90.6,
    "küçük mücenneb diyez": 67.9, "küçük mücenneb bemol": -67.9,
    "büyük mücenneb diyez": 112.9, "büyük mücenneb bemol": -112.9,
}


def get_western_lesson(index: int):
    if index < 0 or index >= len(WESTERN_LESSONS):
        return None
    return WESTERN_LESSONS[index]


def make_chord_function_question(root_name: str, scale_name: str, seed=None):
    rng = random.Random(seed)
    root_pc = NOTE_NAMES.index(root_name)
    chords = diatonic_chords(root_pc, scale_name)
    idx = rng.randint(0, 6)
    chord_root, quality = chords[idx]
    roman = ROMAN[idx]

    if roman in ("I", "VI", "III"):
        correct = "Tonik"
    elif roman in ("IV", "II"):
        correct = "Subdominant"
    else:
        correct = "Dominant"

    label = f"{NOTE_NAMES[chord_root]}{'' if quality=='maj' else quality if quality!='min' else 'm'}"
    return {
        "question": f"{root_name} {scale_name} tonunda {roman} derecesi ({label}) hangi fonksiyona sahiptir?",
        "correct_answer": correct,
        "choices": ["Tonik", "Subdominant", "Dominant"],
    }


def explain_comma_accidental(name: str):
    if name not in COMMA_ACCIDENTALS:
        return None
    cents = COMMA_ACCIDENTALS[name]
    return f"{name}: batı yarım tonundan (~100 cent) farklı olarak yaklaşık {cents:+.1f} cent'lik bir kayma."


def nearest_comma_accidental(cents_deviation: float):
    """Ölçülen bir cent sapmasına (bir notaya göre) en yakın AEU koma
    aksanını bulur — Faz 1'deki koma sesi tanıma özelliğinin temel taşı."""
    best_name, best_diff = None, 999
    for name, cents in COMMA_ACCIDENTALS.items():
        diff = abs(cents_deviation - cents)
        if diff < best_diff:
            best_diff, best_name = diff, name
    return best_name, best_diff
