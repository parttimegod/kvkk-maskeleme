# Açık işler

## Ölçüm

- Tanımlayıcı precision'ı ve isim/adres yanlış pozitifleri ayrı ölçülmeli.
  Şu an temiz kontrol cümlelerinde yalnızca özel nitelikli işaretler sayılıyor.
- Sözlükten bağımsız sekiz cümlede yedi kategori kaçıyor. Kelime eklemekten
  önce farklı anlatımları ve temiz karşı örnekleri içeren daha geniş bir küme
  gerekiyor.
- Model sonuçları yeni konum tabanlı puanlamayla tekrar ölçülmeli.
  Eski sürümlerdeki oranlar yeni raporla doğrudan karşılaştırılamaz.
- Sentetik OCR hasarı gerçek tarama dağılımını temsil etmiyor. Kullanım
  koşullarına uygun ve erişimi yetkili bir veri kümesiyle karşılaştırılmalı.

## Tespit

- Telefon katmanı mobil biçimleriyle, kart katmanı 16 haneyle sınırlı.
- Etiketsiz pasaport, doğum tarihi ve SGK değerleri kaçabiliyor.
- Soyadı yayılımı aynı sözcüğün farklı kişiler veya yerler için kullanımını
  çözemiyor. Tam ad ile soyadı da aynı yer tutucuda birleşmiyor.
- Adres uzatma yalnızca desteklenen cadde/numara zincirlerini kapsıyor.
- Model biçim hatası raporlanıyor; çağıranın bu sonucu otomatik akışta nasıl
  durduracağı daha açık bir arayüzle ele alınabilir.

## Kullanım

- Dosya/esas numarası ve olay ayrıntıları kişiyi belirlenebilir kılabilir;
  mevcut araç bunlar için risk değerlendirmesi yapmıyor.
- CLI'da `--kati` çıktı yazıldıktan sonra çıkış kodunu değiştiriyor.
  Dosya üretmeden durma davranışı ayrı bir seçenek olarak düşünülebilir.
- HTTP adaptörü yerel kullanım için. Kimlik doğrulama, çok kullanıcılı
  servis ve dağıtım ayarları bu sürümde yok.
- PyPI yayını ve bir MCP adaptörü ancak kullanım ihtiyacı oluşursa.
