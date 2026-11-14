# Misyon Akademisi (NASA Space Apps 2026 – Space Mission Design Game)

## Amaç
36 saatlik hackathon için web tabanlı uzay görevi tasarım oyunu. Oyuncu NASA'da yeni başlayan stajyer mühendistir; profesör mentor ile tanışır ve ilk uzay aracını tasarlar. Yarışma sayfası: https://www.spaceappschallenge.org/2026/challenges/space-mission-design-game/

## Karar: sadece web
HTML/CSS/JS, derleme yok (dosyaları doğrudan açın veya GitHub Pages/Netlify ile yayınlayın). exe/apk yok; istenirse sonradan PWA, sonra Electron/Capacitor.

## Akış ve klasörler
- `index.html` — ekranlar: `intro` (video) → `brief` (görev brifingi) → `team` (takım lobisi, isteğe bağlı) → `design` (tasarım odası) → `flight` (fırlatma, 6 aylık görev günlüğü ve rapor)
- `css/style.css`, `js/app.js` (ekran geçişleri), `js/craft.js` (uydu şeması), `js/sim.js` (fırlatma animasyonu, simülasyon, rapor), `js/team.js` (takım modu)
- Yerel deneme: `.claude/launch.json` ile `python -m http.server 8766` (preview_start `misyon-akademisi`).
- `assets/intro.mp4` — GÜNCEL giriş videosu: Masaüstü'ndeki "WhatsApp Video 2026-11-14 at 14.58.00.mp4" (864x496, 12,9 sn, anime tarzı kontrol odası; ekip arkadaşlarından). Yedekler: `assets/intro_site-videosu.mp4` (önceki "site videosu.mp4", 18 sn, NASA logosu görünüyordu) ve `assets/intro_blender.mp4` (Blender ile ürettiğim, 1280x720, 20 sn). Değiştirmek için dosyayı `assets/intro.mp4` adıyla koy. Dosya yoksa yedek ekran çıkar. Video `object-fit:contain` (kırpılmaz, siyah bantlı). DİKKAT: videolarda sol üstte CapCut filigranı var; "site videosu"nda ayrıca NASA logosu/yazısı vardı (kural: logo ve yazı yok). Yeni videonun tamamı denetlenmedi.
- Giriş videosu: kapıdan girme, profesörle tanışma, "tasarıma geçelim", geçiş animasyonu. Video bitince `brief` açılır.

## Kurallar
- Tasarım sade, koyu mavi tema. Kullanıcıyla Türkçe konuşulur, arayüz Türkçe.
- Mentor yüzü videoda görünmez (arkadan/siluet). Brifingte "Prof." rozetli konuşma balonu, yüz yok.
- Videoda yazı/logo yok, yazılar HTML'de eklenir.
- Gerçek NASA logosu kullanma.
- Tasarım dili (GÜNCEL = v3): ORTA TONLU indigo oyun dili. Zemin indigo #33367F (üst bant #262A66), açık kartlar #F1F2FF koyu yazıyla, vurgu hardal #FFC83D (seçili satır, buton) ve mor #7C5CFF (aktif aşama, kaynak çubuğu), hata kırmızı #D93B45. Başlık Bricolage Grotesque, metin Inter. Seçenekler geniş yatay satırlar, butonlar kalın çerçeve + alta düşen gölge, 3 aşama (Fırlatma, Uzay aracı, Bilim yükü), metin "sen" diliyle, emoji yok. Video paleti denendi (kömür-mavi + hologram turkuazı) ve kullanıcı eski hâle döndü; o sürüm `versions/v4-video-paleti/` içinde yedekte. Renkler `css/style.css` başındaki `:root`.
- SÜRÜMLER: `versions/v3-indigo-takim/` = GÜNCEL (indigo/hardal/mor, takım modu ve simülasyon dahil; kökle birebir aynı). `versions/v4-video-paleti/` = denenip geri alınan video paleti. `versions/v1-oyunsu-neseli/` = parlak ve neşeli (mavi/sarı/mercan/nane/mor, Fredoka) sürüm. `versions/v2-indigo-satirlar/` = GÜNCEL beğenilen sürüm (indigo zemin, hardal+mor, Bricolage+Inter, yatay satır seçenekler). İkisi de kendi başına çalışır. Geri dönmek için içindeki index.html, css/, js/ proje köküne kopyalanır. Önemli bir tasarım değişikliğinden önce yeni bir `versions/vN-...` yedeği al. Daha önce reddedilen yönler (8, siyah-mor dahil): NASA paleti, kehribar+koyu, krem belge, sert NASA kurumsal, soft açık tema, malzeme paleti/tablo; hepsi "yapay zeka gibi" bulundu.

## Planlanan adımlar
1. (bitti) İskelet + intro + brifing
1b. (bitti) Tasarım odası (üç aşamalı: Fırlatma / Uzay aracı / Bilim yükü, rozetli kartlar, sağda şema ve kaynaklar): `js/data.js` (parça verileri, MISSION limitleri), `js/design.js` (hesap, 12 kontrol, kaynak çubukları, inceleme). Bütçe 3,2M$, kütle 14 kg, bilim hedefi 40, ömür 6 ay (denge taraması: 42 geçerli tasarım; eski 2,5M$/12 kg ile yalnızca 4 vardı). Örnek geçerli tasarım: 6U + büyük panel + küçük batarya + S-bant + reaksiyon tekerleği + küçük roket + 600 km + kamera + manyetometre.
2. (bitti, bkz. 1b) Tasarım odası: fırlatıcı, yörünge, enstrüman, kaynak çubukları (kütle, güç, bütçe, veri, haberleşme, ömür)
3. (bitti) Fırlatma + simülasyon + olaylar + puan + rapor: `js/sim.js`. Tasarım onaylanınca "Fırlat" butonu; roket boyutu fırlatıcıya göre; 6 ay günlüğü, 3 rastgele olay (güneş fırtınası, yer istasyonu kesintisi, enstrüman arızası, bütçe kesintisi; 4'ünden 3'ü), olay sonucu yalnızca tasarım marjlarına bağlı; puan = bilim %40 + kaynak verimi %30 + dayanıklılık %30; "neden böyle oldu" açıklamaları, ipuçları, benzer gerçek görev türü, "Tekrar simüle et". Atla butonu var.
3b. (bitti) Takım modu: `js/team.js` + `#team` ekranı. 4 rol, her birinin sorumlu olduğu parçalar ve GİZLİ hedefi: Görev planlayıcı (yörünge, roket; bütçede >=0,40M$ pay), Uzay aracı mühendisi (gövde, panel, batarya, yönelim; güç marjı >=%15), Haberleşme sorumlusu (telsiz; indirme >=1,3x veri), Bilim sorumlusu (enstrüman; bilim >=55). 42 geçerli tasarımın 8'i dört hedefi birden tutturuyor (hedefler çatışır ama çözülebilir). İki biçim: (1) çevrimiçi oda: PeerJS (WebRTC, unpkg CDN, herkese açık PeerJS aracısı gerekir), 4 harfli oda kodu, kurucu (host) otorite, istekler host'a gider, host durumu yayar, sohbet var, boş rolleri herkes düzenler; fırlatma sonucunu host üretip yayar (iki oyuncuda birebir aynı sonuç, iki sekmeyle doğrulandı); (2) aynı ekranda: tek cihaz, rol çubuğundan sıra devri. Raporda "Ekip uyumu" (rol hedefleri tutturuldu/tutturulamadı) ve puan: bilim %30 + verim %20 + dayanıklılık %20 + ekip %30. Eşikler `ROLES` içinde (`js/team.js`); değiştirirsen tasarım uzayını yeniden tara (kaç tasarım hedefleri karşılıyor?).
4. Eğitim kutuları, 2 yeni görev (yangın gözcüsü, buz Ay'ı), kariyer ilerlemesi, yayınlama (GitHub Pages)

## Açık konular
- Mentor adı, ilk görev değerleri (bütçe/kütle/güç) taslak.
- Çok oyunculu altyapı seçimi (PeerJS veya Firebase).

## Blender giriş animasyonu (devam eden iş)
- Sahne betiği: `blender/intro_scene.py` (Blender 5.1.1, `C:\Program Files\Blender Foundation\Blender 5.1lender.exe`). Arka planda çalışır (pencere yok), Cycles + OptiX (RTX 4060). Kullanıcının makinesinde Blender penceresi OpenGL 4.3 hatası veriyor (Windows Grafik ayarında blender.exe "Yüksek performans" yapılmalı); arka plan modu bundan etkilenmez.
- İçerik (18 sn, 24 fps, 1280x720): koridor ve kapı açılır → laboratuvar → profesör arkadan (yüzsüz), el sallar, tahtada yörünge çizilir → masadaki uydu maketine yaklaşma → parlama geçişi (kare 312) → uzayda parça parça kurulan uydu, Dünya kıyısı, ay. Videoda yazı yok. Son kare siteye benzer.
- Önizleme: `blender -b -P blender/intro_scene.py -- preview ÇIKTI_KLASÖRÜ 1 61 121 ...` (kare numaraları)
- Tam video: `blender -b -P blender/intro_scene.py -- render assets\intro_render 36 blender\progress.log` (36 = örnek sayısı). Tahmini süre ~35 dk (kare başı ~5 sn). Çıktı `assets\intro_render0001-0432.mp4` adıyla çıkar; bitince `assets\intro.mp4` olarak yeniden adlandır (site bu adı oynatır).
- DURUM: önizlemeler onaylandı; tam render iki kez kesildi (kullanıcı durdurdu), 66/432 kare çizilmişti. `assets/intro.mp4` henüz YOK (site yedek ekranı gösterir). Yapılacak: render'ı baştan çalıştır, bitince yeniden adlandır, sitede dene.
- Blender 5 notları: video çıktısı için önce `image_settings.media_type='VIDEO'`; `action.fcurves` kaldırıldı (kullanma). Sadece kendi süreçlerini kapat (tüm `blender.exe` süreçlerini değil: kullanıcının penceresi olabilir; `CommandLine` içinde `intro_scene.py` geçenleri hedefle).

### Blender v2 (GERÇEKÇİ sürüm, güncel; v1 `intro_scene.py` stilize/kutu gibi bulunup reddedildi)
- Betik: `blender/intro_scene_v2.py`, sahne dosyası `blender/misyon_intro_v2.blend` (kullanıcı Blender'da açıp bakıyor). 20 sn, 480 kare, kare 336'da parlama + uzaya geçiş.
- Neler gerçekçi: gerçek pencere ve kapı boşlukları, gün batımı gökyüzü (güneş pencereden girer, profesörün gölgesi kitaplığa düşer), parke zemin, kitaplık, tezgah, masa, dizüstü, globe, saksı, roket maketleri, tavan lambaları, koridor ayrıntıları; tüvit ceketli, eklemli kollu, parmaklı, beyaz saçlı profesör (yalnızca arkadan, yüzsüz); yürüme sarsıntılı kamera + alan derinliği; uzayda bulutlu/kıtalı Dünya, atmosfer, altın folyolu uydu parça parça kurulur.
- Önizleme: `blender -b -P blender/intro_scene_v2.py -- preview KLASÖR 1 130 200 ...` (ortam değişkenleri `PREV_PCT`=yüzde, `PREV_SAMPLES`). Tam video: `-- render assets\intro_render 48 blender\progress.log`. Tam çözünürlükte ~6 sn/kare => ~45-50 dk. Çıktı `assets\intro_render0001-0480.mp4`; bitince `assets\intro.mp4` olarak yeniden adlandır.
- Blender 5 tuzakları: `bpy.ops.object.transform_apply` varsayılan olarak konumu da uygular (kapı kaydı); `location=False, rotation=False, scale=True` kullan. Sol kolun öne uzanması için X dönüşü POZİTİF.
- DURUM: TAMAMLANDI. Tam render alındı (480 kare, 48 örnek, ~35 dk), `assets/intro.mp4` yerinde (5,4 MB, 20 sn, 1280x720). Sitede oynuyor ve bitince brifinge geçiyor (doğrulandı). Yerel `python -m http.server` Range istekleri desteklemediği için sarma (seek) denemesi başa dönebilir; GitHub Pages/Netlify'da sorun olmaz. Telefonda dikey ekranda video `object-fit:cover` ile kırpılır.

## Yayın (GitHub Pages)
- Depo: https://github.com/grkm2802/misyon-akademisi (herkese açık; Pages için gerekli)
- Canlı site: https://grkm2802.github.io/misyon-akademisi/ (main dalı, kök klasör; derleme yok)
- Güncellemek için: değişiklikleri yap, sonra `git add -A`, `git commit -m "..."`, `git push`. Pages birkaç dakika içinde yeniler.
- `.gitignore` dışında tutulanlar: `.claude/`, `*.blend`, ilerleme kayıtları, `assets/intro_blender.mp4` ve `assets/intro_site-videosu.mp4` (video yedekleri). Siteye yalnızca `assets/intro.mp4` girer. `versions/` depoda (bulutta yedek olsun diye) ve canlı sitede `/versions/...` altında açılır.
- Çevrimiçi takım odası PeerJS'in herkese açık aracısını kullanır (HTTPS'te çalışır). Yazı tipleri Google Fonts'tan gelir.
- Videonun NASA logosu/yazısı ve CapCut filigranı konusu açık (kullanıcıya bildirildi); yayın öncesi kontrol edilmeli.
