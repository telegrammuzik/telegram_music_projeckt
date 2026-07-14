"""
Ek: İlerleme takibi + Akıllı koç + Kişisel müzik profili paneli + Yedekleme/
dışa aktarma. Hepsi Supabase'deki tek bir 'progress_events' tablosunu paylaşır
(Faz 0'daki "ortak tablo" prensibi — her özellik için ayrı tablo değil).

ÖNEMLİ — bu modül de canlı Supabase ile test EDİLEMEDİ. Kullanmadan önce
Supabase'de şu tabloyu oluştur:

    create table progress_events (
        id bigint generated always as identity primary key,
        user_id bigint not null,
        category text not null,      -- 'solfej', 'egzersiz', 'armoni', 'beste' vb.
        detail text,
        score numeric,
        created_at timestamptz default now()
    );
"""

import random
from collections import Counter
from datetime import datetime, timedelta

from core.db import get_client


def make_daily_challenge(output_wav_path: str, seed=None):
    """Ek: Günlük mini meydan okuma. Solfej oyunlarından rastgele birini seçip
    döner (schedule özelliğiyle her gün otomatik gönderilmek üzere main.py'de
    bir job olarak tetiklenmesi planlanıyor)."""
    from modules.solfege_games import make_interval_question, make_note_id_question

    rng = random.Random(seed)
    game = rng.choice(["interval", "note_id"])
    if game == "interval":
        q = make_interval_question(output_wav_path, seed=seed)
        return {"type": "aralık tanıma", **q}
    else:
        q = make_note_id_question(output_wav_path, seed=seed)
        return {"type": "nota tanıma", **q}


def log_event(user_id: int, category: str, detail: str = None, score: float = None):
    client = get_client()
    client.table("progress_events").insert({
        "user_id": user_id, "category": category, "detail": detail, "score": score,
    }).execute()


def get_recent_events(user_id: int, days: int = 30):
    client = get_client()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    result = (
        client.table("progress_events")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", since)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def suggest_next_practice(user_id: int):
    """Akıllı koç: en az çalışılan / en düşük skorlu kategoriyi önerir."""
    events = get_recent_events(user_id, days=14)
    if not events:
        return "Henüz kayıtlı pratik geçmişin yok — Faz 4 (egzersizler) veya Faz 5 (solfej oyunları) ile başlayabilirsin."

    counts = Counter(e["category"] for e in events)
    all_categories = ["egzersiz", "solfej", "armoni", "nota_okuma", "beste"]
    least_practiced = min(all_categories, key=lambda c: counts.get(c, 0))

    scores_by_cat = {}
    for e in events:
        if e.get("score") is not None:
            scores_by_cat.setdefault(e["category"], []).append(e["score"])
    lowest_score_cat = None
    lowest_avg = 999
    for cat, scores in scores_by_cat.items():
        avg = sum(scores) / len(scores)
        if avg < lowest_avg:
            lowest_avg, lowest_score_cat = avg, cat

    if lowest_score_cat and lowest_avg < 70:
        return f"Son zamanlarda '{lowest_score_cat}' konusunda skorların düşük (ortalama %{lowest_avg:.0f}) — biraz daha pratik yapmayı öner."
    return f"'{least_practiced}' konusuna son 2 haftada hiç ya da az değinmemişsin — bugün ona ayırmayı düşün."


def weekly_summary(user_id: int):
    events = get_recent_events(user_id, days=7)
    if not events:
        return "Bu hafta kayıtlı bir aktivite yok."

    counts = Counter(e["category"] for e in events)
    lines = [f"Bu hafta toplam {len(events)} aktivite:"]
    for cat, count in counts.most_common():
        lines.append(f"- {cat}: {count} kez")
    return "\n".join(lines)


def daily_streak(user_id: int):
    """Kaç gün üst üste (bugün dahil) en az bir aktivite yapılmış, sayar."""
    events = get_recent_events(user_id, days=60)
    if not events:
        return 0

    days_active = set()
    for e in events:
        dt = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))
        days_active.add(dt.date())

    streak = 0
    day = datetime.utcnow().date()
    while day in days_active:
        streak += 1
        day -= timedelta(days=1)
    return streak
