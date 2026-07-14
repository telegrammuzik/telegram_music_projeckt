"""
Ek: Otomatik yedekleme / dışa aktarma. Kullanıcının fikir bankasındaki
(idea_bank) dosya referanslarını tek bir zip'te toplar. Not: dosyaların
kendisi Supabase Storage'da tutulmalı — bu fonksiyon sadece "referansları
indirip zip'leme" akışının iskeletidir, gerçek dosya indirme kısmı
Supabase Storage entegrasyonu netleşince tamamlanmalı.
"""

import zipfile
import os

from modules.idea_bank import list_ideas


def export_user_ideas_as_zip(user_id: int, local_file_paths_by_idea_id: dict, output_zip_path: str):
    """
    local_file_paths_by_idea_id: {idea_id: yerel_dosya_yolu} — bot, Supabase
    Storage'dan dosyaları indirip geçici bir yere koyduktan sonra bu sözlüğü
    doldurup burayı çağıracak.
    """
    ideas = list_ideas(user_id)
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for idea in ideas:
            local_path = local_file_paths_by_idea_id.get(idea["id"])
            if local_path and os.path.exists(local_path):
                arcname = f"{idea.get('title') or idea['id']}_{os.path.basename(local_path)}"
                zf.write(local_path, arcname)
    return output_zip_path
