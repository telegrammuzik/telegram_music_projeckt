"""
Ek: Fikir bankası / sesli not defteri + Beste: besteci defteri (versiyon
karşılaştırma). Supabase'de saklanır.

ÖNEMLİ — bu modül canlı bir Supabase bağlantısıyla test EDİLEMEDİ (bu ortamda
gerçek bir Supabase projesine bağlanamıyorum). Kod mantığı doğru olmalı ama
ilk canlı denemede küçük düzeltmeler gerekebilir. Kullanmadan önce Supabase'de
şu tabloyu oluşturman gerekiyor (SQL Editor'de çalıştır):

    create table ideas (
        id bigint generated always as identity primary key,
        user_id bigint not null,
        title text,
        tag text,
        file_path text,
        project_name text,
        created_at timestamptz default now()
    );
"""

from core.db import get_client


def save_idea(user_id: int, title: str, tag: str, file_path: str, project_name: str = None):
    client = get_client()
    result = client.table("ideas").insert({
        "user_id": user_id,
        "title": title,
        "tag": tag,
        "file_path": file_path,
        "project_name": project_name,
    }).execute()
    return result.data


def list_ideas(user_id: int, tag: str = None, project_name: str = None):
    client = get_client()
    query = client.table("ideas").select("*").eq("user_id", user_id)
    if tag:
        query = query.eq("tag", tag)
    if project_name:
        query = query.eq("project_name", project_name)
    result = query.order("created_at", desc=True).execute()
    return result.data


def list_projects(user_id: int):
    """Besteci defteri: aynı project_name altında gruplanmış fikirleri/versiyonları listeler."""
    ideas = list_ideas(user_id)
    projects = {}
    for idea in ideas:
        proj = idea.get("project_name") or "Etiketsiz"
        projects.setdefault(proj, []).append(idea)
    return projects
