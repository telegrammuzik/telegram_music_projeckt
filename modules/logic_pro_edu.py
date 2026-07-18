"""
Faz 9: Logic Pro eğitimi — v2, çok daha kapsamlı.

Türkçe anlatım, programın kendi arayüzünde İngilizce geçen isimler (Flex Time,
Track Stack, Smart Tempo, Space Designer vb.) İngilizce/orijinal haliyle
korunuyor — çünkü program menülerinde onları öyle göreceksin.

Kapsam notu: v1'de sadece 6 çok kısa paragraf vardı ("çok kısıtlı" eleştirisi
haklıydı). Bu sürüm gerçek workflow'ları adım adım anlatıyor ve Logic'in
stok plugin/enstrüman kütüphanesini (Alchemy, Sculpture, ES2, Retro Synth,
Sampler, Drummer, Space Designer, ChromaVerb, Vintage EQ/Compressor koleksiyonu,
Amp Designer/Pedalboard vb.) tek tek tanıtıyor.

Dürüstlük notu: Logic Pro sık güncelleniyor; menü/kısayol konumları versiyon
arasında hafifçe değişebilir. Burada anlatılanlar uzun süredir stabil olan,
temel workflow'lar — versiyon numarası belirtmeden genel geçer bilgi.
Logic VST DEĞİL, Audio Unit (AU) plugin formatını kullanır (Mac'e özgü) —
üçüncü parti "plugin/VST" araştırırken Mac için "AU" sürümünü aramalısın.
"""

LESSONS = {
    "1. Proje Kurulumu ve Kayıt": (
        "Yeni proje açarken şablon (template) seçebilirsin — 'Empty Project' "
        "boş başlamak, 'Songwriter'/'Hip Hop'/'Electronic' gibi hazır şablonlar "
        "ise önceden ayarlı track'lerle (davul, bas, enstrüman) başlamak içindir.\n\n"
        "Track eklemek için sol üstteki '+' butonuna bas: 'Audio' (mikrofon/gitar "
        "kaydı için), 'Software Instrument' (MIDI ile çalınan sanal enstrüman "
        "için) ya da 'Drummer' (yapay zeka destekli otomatik davulcu) seçebilirsin.\n\n"
        "Kayıt: kırmızı 'Record' butonuna (ya da R tuşuna) bas. 'Count-in' "
        "(Preferences > Recording) kayıt öncesi metronomla sayım verir, işine "
        "yarayabilir. 'Cycle' modu (C tuşu) seçili bir bölgeyi tekrar tekrar "
        "kaydetmeni sağlar — her tur otomatik bir 'Take' olarak 'Take Folder' "
        "içinde birikir, sonra en iyi performansı (ya da parçaları birleştirip "
        "'comping' yaparak) seçersin."
    ),
    "2. Comping (Take Seçme/Birleştirme)": (
        "Take Folder'ı açtığında (üzerine tıkla ya da üçgen okuna bas) her "
        "kaydettiğin 'take' ayrı bir şerit olarak görünür. Bir take'in tamamını "
        "seçmek için üzerine tıkla; ama asıl güç 'Quick Swipe Comping'de: fare "
        "ile bir take üzerinde SÜRÜKLEYEREK (swipe) sadece o bölümü seçebilirsin "
        "— yani 1. take'in nakaratını, 2. take'in verse'ünü birleştirip 'en iyi "
        "performansı' parça parça inşa edebilirsin. Seçtiğin parçalar arasında "
        "otomatik küçük crossfade'ler oluşur (kesintisiz geçiş için)."
    ),
    "3. MIDI Düzenleme (Piano Roll)": (
        "Bir MIDI (Software Instrument) bölgesine çift tıklayınca Piano Roll "
        "açılır — notaları görsel olarak (yatay=zaman, dikey=perde) görürsün.\n\n"
        "'Quantize' (Q tuşu ya da sağ tık menüsü > Quantize) notaları en yakın "
        "ritim ızgarasına (1/16, 1/8 triplet vb.) oturtur — insan kaynaklı ufak "
        "zamanlama hatalarını düzeltir, ama %100 quantize bazen 'robotik' "
        "hissettirebilir, %50-70 gibi kısmi quantize daha doğal durabilir.\n\n"
        "'Velocity' (nota vurgu/dinamik gücü) Piano Roll'un alt kısmındaki "
        "editörden ayarlanır — daha gerçekçi bir performans için tüm notaları "
        "aynı velocity'de bırakma, biraz varyasyon ekle.\n\n"
        "'Transform' penceresi (Piano Roll içinde) toplu nota işlemleri (ör. "
        "tüm notaları bir aralık kaydır, belirli bir aralıktaki notaları sil) "
        "için kullanılır."
    ),
    "4. Flex Time ve Flex Pitch": (
        "Flex Time: bir audio kaydının ZAMANLAMASINI (transient'lara dokunarak) "
        "esnetmeni sağlar — mesela bir gitar/davul kaydındaki ritim hatasını "
        "audio'yu yeniden kaydetmeden düzeltebilirsin. Track'in Flex düğmesini "
        "aç, bir algoritma seç (Rhythmic, Monophonic, Polyphonic, Speed - "
        "kaynağa göre doğru algoritma önemli, ör. vokal için Monophonic).\n\n"
        "Flex Pitch: MONOFONİK bir kayıtta (vokal, tek nota çalan enstrüman) "
        "PERDEYİ (pitch) düzeltmeni sağlar — Piano Roll'da audio bölgesi açılınca "
        "her 'nota' bir blok olarak görünür, bunları sürükleyerek doğru perdeye "
        "taşıyabilir, hatta vibrato/formant ayarlayabilirsin. Bu, oto-tune benzeri "
        "bir düzeltme aracıdır."
    ),
    "5. Enstrümanlar — Sentezleyiciler": (
        "Logic'in kendi sentezleyicileri (Software Instrument track'inde "
        "'Instrument' slotuna tıklayınca listede görünür):\n\n"
        "- Alchemy: en güçlü/esnek sentezleyici, spektral/granular/additive "
        "sentez yapabilir, hazır preset kütüphanesi çok geniş.\n"
        "- ES2: klasik subtractive (analog tarzı) synth, 3 osilatör.\n"
        "- Sculpture: fiziksel modelleme (bir telin/yüzeyin nasıl titreştiğini "
        "simüle eder), çok organik/gerçekçi tel/üflemeli tınılar üretebilir.\n"
        "- Retro Synth: analog/FM/sitar-tarzı vintage synth taklitleri."
    ),
    "6. Enstrümanlar — Örnekleyiciler (Samplers)": (
        "- Quick Sampler: bir audio dosyasını (ya da kaydı) sürükle-bırak "
        "yapıp saniyeler içinde çalınabilir bir enstrümana çeviren basit/hızlı "
        "sampler. Loop noktası, ADSR zarfı ayarlanabilir.\n\n"
        "- Sampler (eski adıyla EXS24'ün yerini aldı): çok katmanlı, "
        "velocity-switch'li profesyonel örnekleme motoru; kendi örnek "
        "kütüphaneni (ör. gerçek bir enstrümandan kaydettiğin notalar) buraya "
        "yükleyip tüm klavyeye yayabilirsin (mapping).\n\n"
        "Bu, Türk çalgıları (tulum, zurna, ney vb.) için EN gerçekçi yöntemdir: "
        "birkaç temiz nota kaydedip Sampler/Quick Sampler'a yüklersen, botun "
        "sentezinden çok daha gerçek bir tını elde edersin."
    ),
    "7. Drummer Track (Yapay Zeka Davulcu)": (
        "Track ekle > 'Drummer' seç. Bir davulcu karakteri (tür bazlı: Pop, "
        "Rock, Songwriter, Electronic...) seç. Sağdaki panelden 'X/Y pad' ile "
        "davulcunun karmaşıklığını (complexity), dinamiğini (loudness/energy), "
        "fill sıklığını canlı ayarlarsın — davulcu senin seçimlerine göre "
        "performansı gerçek zamanlı üretir/günceller.\n\n"
        "Bir bölümü (intro/verse/chorus) seçip 'Fill' ekleyebilir, 'Follow' "
        "özelliğiyle davulcunun başka bir track'i (ör. bas) takip etmesini "
        "sağlayabilirsin."
    ),
    "8. Mixer ve Sinyal Akışı": (
        "X tuşu Mixer'ı açar. Her track'in kendi 'channel strip'i vardır: "
        "üstte Instrument/plugin slotları (Audio FX), altta Volume (fader), "
        "Pan, Sends (efekt yollama, ör. bir reverb bus'ına), en altta Solo (S) "
        "ve Mute (M).\n\n"
        "'Bus' mantığı: birden fazla track'i tek bir 'Aux' kanalına Send ile "
        "gönderip (ör. hepsini aynı reverb'e), o Aux'ta TEK bir reverb plugin'i "
        "çalıştırmak, her track'e ayrı ayrı reverb koymaktan hem daha verimli "
        "(CPU) hem de daha 'tutarlı bir oda hissi' verir.\n\n"
        "'Track Stack' (Summing ya da Folder Stack) benzer track'leri (ör. tüm "
        "davul mikrofonları) tek bir grup fader'da toplamana yarar."
    ),
    "9. Stok Mixing Plugin'leri": (
        "- Channel EQ: 8 bantlı parametrik EQ, her mixte temel araç.\n"
        "- Compressor: birden fazla 'circuit type' (Platinum Digital, Vintage "
        "VCA, Vintage Opto, FET vb.) taklit eder, her biri farklı karakterde "
        "sıkıştırma yapar.\n"
        "- Multipressor: çok bantlı compressor (ör. sadece bas frekanslarını "
        "sıkıştırmak için).\n"
        "- Space Designer: convolution (gerçek mekan/impuls yanıtı temelli) "
        "reverb, çok gerçekçi oda/salon simülasyonu.\n"
        "- ChromaVerb: daha modern, algoritmik/renkli bir reverb, CPU dostu.\n"
        "- Tape (vintage tape saturation/warmth), Vintage EQ Collection (analog "
        "EQ taklitleri: Pultec-tarzı, API-tarzı, SSL-tarzı).\n"
        "- Bass Amp Designer / Amp Designer / Pedalboard: gitar/bas amfi ve "
        "efekt pedalı simülasyonları, DI kaydı sonradan 're-amp' etmek için de kullanılır."
    ),
    "10. Otomasyon (Automation)": (
        "A tuşu Automation modunu açar/kapatır. Track başlığındaki açılır "
        "menüden hangi parametreyi (Volume, Pan, bir plugin'in belirli bir "
        "kontrolü) otomatikleştireceğini seçersin, sonra o çizgi üzerine nokta "
        "ekleyip (tıkla) çizgiyi çekiştirerek zaman içindeki değişimi çizersin.\n\n"
        "Modlar: 'Read' (otomasyonu çalar ama değiştirmezsin), 'Touch' "
        "(fader'a dokunduğun sürece kaydeder, bırakınca son değere döner), "
        "'Latch' (dokunduğun andan itibaren kaydetmeye devam eder), 'Write' "
        "(baştan sona her şeyi ezer, dikkatli kullan)."
    ),
    "11. Smart Tempo ve Arrangement": (
        "Smart Tempo: sabit tempoda kaydetmediğin (ör. metronomsuz, canlı "
        "çalınmış) bir kaydı analiz edip, projenin tempo haritasını o kayda "
        "UYDURABİLİR (ya da tam tersi, kaydı projenin tempo haritasına "
        "uydurabilir). Karma kaynaklı (farklı oturumlardan) parçaları "
        "birleştirirken çok işe yarar.\n\n"
        "Arrangement Marker'lar (Intro/Verse/Chorus/Bridge/Outro gibi) üst "
        "cetvele eklenir; bir bölümü sürükleyerek TÜM track'lerdeki o bölümü "
        "aynı anda taşırsın (şarkı yapısıyla oynamak için, ör. bir nakaratı "
        "çoğaltmak) — parça parça elle taşımaktan çok daha hızlı."
    ),
    "12. Bounce/Dışa Aktarma ve Kısayollar": (
        "Bitirdiğin projeyi paylaşılabilir bir ses dosyasına çevirmek için "
        "File > Bounce > Project or Selection (ya da Cmd+B). PCM (WAV/AIFF) "
        "format, örnekleme hızı/bit derinliği (ör. 44.1kHz/24-bit) seçilir.\n\n"
        "Sık kullanılan kısayollar: Cmd+S kaydet, Cmd+Z geri al, Space play/stop, "
        "Cmd+K ekran MIDI klavyesini aç/kapat, R kayıt, Q quantize (Piano Roll "
        "içinde nota seçiliyken), X Mixer, A Automation, C Cycle.\n\n"
        "Tipik bir workflow: kaydet (R) → quantize/flex ile zamanlamayı düzelt "
        "→ velocity/dinamikleri elden geçir → mixer'da dengele (X) → gerekirse "
        "otomasyon ekle (A) → bounce et (Cmd+B)."
    ),
    "13. Üçüncü Parti Plugin/VST Kullanımı": (
        "ÖNEMLİ NOKTA: Logic Pro, Windows'taki VST formatını DEĞİL, Mac'e özgü "
        "'Audio Unit' (AU) formatını kullanır. Üçüncü parti bir plugin ararken "
        "'AU' ya da 'AU/VST/AAX' (çoğu üretici hepsini birden sunar) sürümünü "
        "indirmelisin — sadece 'VST' yazan bir indirme Logic'te görünmez.\n\n"
        "Kurulum: plugin'in kendi yükleyicisini (installer) çalıştırdıktan "
        "sonra Logic'i yeniden başlat; ilk açılışta 'yeni plugin'leri tara' "
        "sorabilir, onayla. Plugin bir Software Instrument ya da Audio FX "
        "slotunda 'Audio Units' alt menüsünde üretici adına göre listelenir.\n\n"
        "Ücretsiz/uygun fiyatlı AU plugin kaynakları (araştırmaya değer): "
        "Spitfire Audio LABS (ücretsiz orkestral örnekler), Surge XT (ücretsiz "
        "açık kaynak synth), TAL Software'in ücretsiz eklentileri, Valhalla "
        "DSP'nin ücretsiz reverb'ü (Valhalla Supermassive/Freq Echo)."
    ),
}


def list_topics():
    return list(LESSONS.keys())


def get_lesson(topic: str):
    return LESSONS.get(topic)
