"""
Ortak Supabase bağlantısı (Faz 0). v1'de henüz hiçbir modül bunu kullanmıyor
(Faz 1 sadece dosya işliyor, veri saklamıyor) ama ileride ilerleme/skor/fikir
bankası gibi her modül tek bir yerden gelen bu client'ı kullanacak.
"""

from supabase import create_client, Client
from core.config import SUPABASE_URL, SUPABASE_SECRET_KEY

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SECRET_KEY ayarlanmamış. "
                "Render'da Environment sekmesinden ekle."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    return _client
