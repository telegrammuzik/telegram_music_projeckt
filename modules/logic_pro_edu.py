"""
Faz 9: Logic Pro eğitimi. Türkçe anlatım, program içi isimler (İngilizce)
orijinal haliyle korunuyor. İçerik statik metin — konu başlıklarına göre
organize, buton tabanlı gezinme için main.py'de menüye bağlanacak.
"""

LESSONS = {
    "Kayıt (Recording)": (
        "Yeni bir ses/enstrüman track'i eklemek için sol üstteki '+' butonuna bas. "
        "Kayıt yapmak için kırmızı 'Record' butonuna (ya da R tuşuna) bas. "
        "'Cycle' modu (C tuşu) açıkken seçili bölgeyi tekrar tekrar kaydedip "
        "'Take Folder' içinde en iyi performansı seçebilirsin."
    ),
    "MIDI Düzenleme": (
        "Piano Roll (MIDI çift tıklayınca açılır) ile notaları görsel olarak "
        "düzenlersin. 'Quantize' (Q tuşu ya da sağ tık menüsü) notaları en "
        "yakın ritim ızgarasına oturtur. 'Velocity' (nota hızı/dinamiği) sol "
        "alttaki editörden ayarlanır."
    ),
    "Enstrümanlar/Pluginler": (
        "'Library' panelinden (Y tuşu) hazır enstrüman/preset'ler seçilir. "
        "Kendi Software Instrument'ını eklemek için track'in 'Instrument' "
        "slotuna tıkla. Alchemy, Sampler gibi Logic'in kendi sentezleyicileri "
        "de bu şekilde açılır."
    ),
    "Mixer": (
        "X tuşu ile Mixer'ı açarsın. Her track için Volume (fader), Pan, ve "
        "'Sends' (efekt gönderme, örn. reverb/delay bus'a) buradan ayarlanır. "
        "Bir track'i 'Solo' (S) ya da 'Mute' (M) yapabilirsin."
    ),
    "Otomasyon (Automation)": (
        "A tuşu ile Automation modunu açarsın. Volume, Pan ya da herhangi bir "
        "plugin parametresi zaman içinde değişecek şekilde 'otomatikleştirilebilir' "
        "— örneğin bir bölümde ses kademeli kısılabilir."
    ),
    "Kısayollar/Workflow": (
        "Cmd+S: kaydet. Cmd+Z: geri al. Space: play/stop. Cmd+K: MIDI klavyeyi "
        "aç/kapa. Sık kullanılan bir workflow: kaydet (R) → quantize (Q) → "
        "velocity düzenle → mixer'da dengele (X)."
    ),
}


def list_topics():
    return list(LESSONS.keys())


def get_lesson(topic: str):
    return LESSONS.get(topic)
