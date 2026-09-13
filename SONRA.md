# Sonra

Aklıma gelen ama şimdi yapmayacağım şeyler.

## Aşama 2 — model katmanı (tamamlandı, ADRES'in etiketli-konum sınırı da kapandı)
İsim, adres, kurum tespiti Ollama üzerinden bağlandı. İlk ölçümde (140
sentetik belge, adlar hep "Davacı Ahmet Yılmaz" gibi önceden etiketlenmiş
sabit kalıplarda, sabit bir isim listesinden): AD 220/220, ADRES 40/40,
KURUM 60/60 -- üçü de %100. Bu %100 bir üst sınırdı: cümle içinde
etiketsiz geçen isimleri, günlük kelime olarak da kullanılan
isim-kelimelerini (Deniz, Umut, Şafak, Barış, Güneş gibi) günlük kelime
bağlamında, ya da yanlış yazılmış isimleri hiç sınamıyordu.

`zor_metin` üreticisi eklenince (isimler etiketsiz düzyazıda, çıplak
soyadıyla, hâl ekiyle, günlük kelimeyle çakışan bir adla) AD recall'ı
%96.7'ye düştü. Kaçan her isim aynı biçimdeydi: kişi bir kez tam adıyla
anılıp sonra yalnızca soyadıyla anılıyordu ("Güneş Yıldız'ın beyanı
alınmış... dinlenen Yıldız, beyanında..."), ve kaçanlar günlük kelimeyle
çakışan soyadlarda yoğunlaşıyordu (Aydın, Kaya, Yıldız, Aslan, Arslan,
Öztürk, Yıldırım). `soyadi_yay` bu yayılımı deterministik biçimde
yapınca recall %99.5'e çıktı (180 belge, 9 tür × 20: AD 378/380, ADRES
40/40, KURUM 60/60).

ADRES aynı sınırı taşıyordu: üreticide adres hep etiketli bir konumda
duruyordu, %100 yalnızca "etiketten oku" testiydi. `zor_adres` eklenince
(adres sözcüğü kendisinden sonra gelerek, tam idari zincir olarak,
sadece mahalle adıyla ya da hiçbir adres sözcüğü olmadan) ADRES recall'ı
%96.4'e düştü. Kaçan beşin hepsi aynı biçimdeydi ve gerçekte kaçmamıştı
-- **yarım maskelenmişti**: model "Kızılay Mahallesi 28. Cadde No: 20"
ifadesinden yalnızca "Kızılay Mahallesi"yi döndürüyordu, çıktı da
"Tebligat <ADRES_1> 28. Cadde No: 20 numarasına yapılmıştır" oluyordu --
sokak ve kapı numarası açıkta kalıyordu. Bunu yakalayan, `olcum.py`'nin
konum örtüşmesi değil birebir `(tür, değer)` eşleşmesi araması: örtüşme
sorulsaydı "Kızılay Mahallesi" etiketli adresle örtüştüğü için bulundu
sayılırdı. `adresi_genislet`, bir ADRES bulgusunu ardından gelen
cadde/sokak/numara/kat zincirine kadar deterministik olarak uzatınca
recall %100'e çıktı (200 belge, 10 tür × 20: AD 378/380, ADRES 140/140,
KURUM 60/60).

Yerel model kullanılıyor, veri makineden çıkmıyor.

Hâlâ kapsanmayanlar:
- Yanlış yazılmış (misspelled) adlar ve adresler.
- OCR ile bozulmuş adlar ve adresler.

Bu, aşağıdaki Ölçüm bölümünde özel nitelikli veri recall'ı için kayıtlı
olan sınırla aynı sınıftan: ölçüm üreticiyle kelime dağarcığı ya da yapı
paylaştığında, aracı değil üreticiyi ölçmüş oluyorsun.

## KVKK boşlukları
- Özel nitelikli veri artık işaretleniyor (sözlük katmanı hazır, model
  katmanı sağlayıcı verilince). Kalan iş: sözlük kökleri gerçek
  belgelerle sınanmadı, kaçırdıkları ölçülmedi.
- Sözlükte yanlış pozitif ölçümü yok. Şu an yalnızca bilinen tuzaklar
  test edildi ("tanık dinlenmesi", "Aydın"). Gerçek metinde başka
  çakışmalar çıkacaktır.
- Özel nitelikli veri için recall ölçümü yok: sentetik belgelerde
  etiketlenmiş değiller, yalnızca tanımlayıcılar etiketli.
- Yeniden tanımlanma riski ölçülmüyor. Doğrudan tanımlayıcı gitse bile
  dava türü + tarih + mahkeme + olay ayrıntısı kişiyi bulunabilir
  kılabiliyor. k-anonimlik benzeri bir ölçüt düşünülebilir.
- Gerçek anonimleştirme yolu yok. Eşleme silinse bile geri kalan metnin
  değerlendirilmesi gerekiyor; şu an araç bunu yapmıyor.

## Tespit
- Pasaport ve sürücü belgesi numarası.
- SGK sicil numarası.
- Doğum tarihi -- tek başına kişisel veri değil ama isimle birleşince
  tanımlayıcı oluyor.
- Dosya/esas numarası: adliye bağlamında tanımlayıcı olabiliyor,
  maskelenmeli mi tartışılmalı.

## Sentetik veri
- Belge türleri yedi oldu; her tanımlayıcı türü en az bir belgede
  geçiyor. Kalan: gerçek belgelerin biçimiyle karşılaştırılmadı.
- OCR ve ayraç toleransı eklendi. Kalan: gerçek taranmış belgelerde
  ölçülmedi, hangi OCR hatalarının sık olduğu bilinmiyor.
- Ayraç toleransı yalnızca TC, VKN ve IBAN'da. Telefon ve plaka
  desenleri kendi ayraçlarını zaten kabul ediyor ama kontrol hanesi
  olmadığı için gevşetmek riskli.

## Ölçüm
- Recall/precision tablosunu README'ye koy.
- Rakip araçlarla aynı sentetik küme üzerinde karşılaştırma.
- Özel nitelikli veri recall'ı (olcum.py, %100) sentetik.py'nin ürettiği
  cümlelere karşı ölçülüyor, ama o cümleler sözlükteki köklerle aynı
  kelimeleri kullanıyor (ceza_dosyasi() "mahkûmiyeti" diyor, sözlükte
  "mahkumiyet" kökü var; saglik_raporu() "DNA incelemesi" diyor,
  sözlükte "dna" kökü var). Yani ölçüm sözlüğü kendi kelime dağarcığına
  karşı sınıyor -- bağımsız bir doğrulama değil, bir üst sınır.
  tests/test_ozel_nitelikli_bagimsiz.py bunu sentetik.py'den bağımsız
  sekiz cümleyle tekrarladı: sekizden yalnızca biri doğru kategoriyle
  yakalandı. Sözlüğü sentetik olmayan gerçek (anonimleştirilmiş)
  belgelerle sınamak ve gerçek recall'ı ayrıca raporlamak gerekiyor.

## Ambalaj
- PyPI.
- CLI: `anonimle dosya.txt`
- MCP sunucusu olarak sunmak -- evds-mcp ile aynı desen.
