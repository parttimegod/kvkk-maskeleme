# Sonra

Aklıma gelen ama şimdi yapmayacağım şeyler.

## Aşama 2 — model katmanı (tamamlandı)
İsim, adres, kurum tespiti Ollama üzerinden bağlandı ve 140 sentetik
belge üzerinde ölçüldü: AD 220/220, ADRES 40/40, KURUM 60/60 -- üçü de
%100. Yerel model kullanılıyor, veri makineden çıkmıyor.

Ölçümün sınırı, düz konuşmak gerekirse: üretici isimleri "Davacı Ahmet
Yılmaz" gibi önceden etiketlenmiş sabit kalıplara, sabit bir isim
listesinden yerleştiriyor. %100 bir üst sınır -- cümle içinde etiketsiz
geçen isimleri, günlük kelime olarak da kullanılan isim-kelimeleri
(Deniz, Umut, Şafak, Barış, Güneş gibi) günlük kelime bağlamında, ya da
yanlış yazılmış isimleri kapsamıyor. Bu, aşağıdaki Ölçüm bölümünde özel
nitelikli veri recall'ı için kayıtlı olan sınırla aynı sınıftan: ölçüm
üreticiyle kelime dağarcığı ya da yapı paylaştığında, aracı değil
üreticiyi ölçmüş oluyorsun.

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
