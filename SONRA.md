# Sonra

Aklıma gelen ama şimdi yapmayacağım şeyler.

## Aşama 2 — model katmanı (asıl iş)
- İsim tespiti. Desenle olmuyor; günlük kelimeyle çakışan adlar
  (Deniz, Umut, Şafak, Barış, Güneş) bağlam istiyor.
- Adres tespiti.
- Kurum ve şirket adları.
- Yerel model üzerinden, veri makineden çıkmadan.
- Sentetik kümede isim recall'ını ölç; deterministik katmanla karşılaştır.

## Tespit
- Pasaport ve sürücü belgesi numarası.
- SGK sicil numarası.
- Doğum tarihi -- tek başına kişisel veri değil ama isimle birleşince
  tanımlayıcı oluyor.
- Dosya/esas numarası: adliye bağlamında tanımlayıcı olabiliyor,
  maskelenmeli mi tartışılmalı.

## Sentetik veri
- Daha fazla belge türü: tebligat, ihtarname, tutanak, fatura.
- OCR hatası benzetimi -- taranmış belgede "1" ile "l" karışıyor,
  gerçek metinlerde desen bu yüzden kaçıyor.
- Bozuk yazım: boşluksuz TC, noktalı IBAN.

## Ölçüm
- Recall/precision tablosunu README'ye koy.
- Rakip araçlarla aynı sentetik küme üzerinde karşılaştırma.

## Ambalaj
- PyPI.
- CLI: `anonimle dosya.txt`
- MCP sunucusu olarak sunmak -- evds-mcp ile aynı desen.
