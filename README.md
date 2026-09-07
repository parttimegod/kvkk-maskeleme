# kvkk-maskeleme

Türkçe metinlerde kişisel veri tespiti ve **maskeleme**. Belgeleri
işlemeden önce, özellikle bulut tabanlı bir modele göndermeden önce
doğrudan tanımlayıcıları yer tutucuyla değiştirir.

> **Bu araç veriyi anonim hale getirmez.** Maskeleme geri
> döndürülebilir olduğu için çıktı KVKK anlamında hâlâ kişisel veridir.
> Ayrıntı için [KVKK kapsamı](#kvkk-kapsamı) bölümüne bakın.

## Durum

Desen katmanı çalışıyor. Model katmanının **altyapısı hazır, modeli
bağlı değil** — arayüz, cevap çözümleme, birleştirme ve ölçüm yazıldı
ve test edildi; `OllamaSaglayici` verildiğinde devreye giriyor.

| Tür | Durum | Yöntem |
|---|---|---|
| TC kimlik no | ✓ | desen + kontrol hanesi |
| Vergi kimlik no | ✓ | desen + kontrol hanesi |
| IBAN | ✓ | desen + mod-97 |
| Kart numarası | ✓ | desen + Luhn |
| Telefon | ✓ | desen |
| Plaka | ✓ | desen |
| E-posta | ✓ | desen |
| **İsim** | altyapı hazır | model katmanı |
| **Adres** | altyapı hazır | model katmanı |
| **Kurum** | altyapı hazır | model katmanı |

## KVKK kapsamı

Bu bölüm aracın ne yapıp ne yapmadığını netleştirmek için var. Yanlış
anlaşılması uyum açığı doğurur.

### Maskeleme, anonimleştirme değildir

KVKK'da anonim hale getirme, verinin başka verilerle eşleştirilse dahi
hiçbir surette bir kişiyle ilişkilendirilememesi demek. Anonim hale
getirilmiş veri kanun kapsamından çıkar.

Bu araç **takma adlaştırma / maskeleme** yapıyor: `<TC_1>` yer tutucusu
ve yerelde duran bir eşleme tablosu. Eşleme varken işlem geri
alınabiliyor, dolayısıyla:

- Çıktı **hâlâ kişisel veridir**
- Aydınlatma, saklama, güvenlik yükümlülükleri **devam eder**
- Veri KVKK kapsamından **çıkmaz**

Kazanç şurada: veri bulut tabanlı bir modele gönderilirken doğrudan
tanımlayıcılar dışarı çıkmıyor. Bu risk azaltmadır, muafiyet değildir.

Gerçekten anonimleştirmek istiyorsanız eşleme tablosunu silin ve
`geri_al` yolunu kapatın — ama o zaman bile yeniden tanımlanma riski
için metnin geri kalanını değerlendirmeniz gerekir.

### Özel nitelikli veriler kapsam dışında

KVKK madde 6'ya göre özel nitelikli kişisel veriler şunlar: ırk, etnik
köken, siyasi düşünce, felsefi inanç, din, mezhep veya diğer inançlar,
kılık ve kıyafet, dernek/vakıf/sendika üyeliği, sağlık, cinsel hayat,
**ceza mahkûmiyeti ve güvenlik tedbirleri**, biyometrik ve genetik veri.

Bu veriler **maskelenmez, işaretlenir.** Sebebi şu: özel nitelikli veri
bir alan değil, bağlamdır. "Sanık daha önce uyuşturucu kullanmaktan
sabıkalıdır" cümlesinde maskelenecek bir alan yoktur — cümlenin kendisi
veridir. Maskelemeye kalkışmak belgeyi anlamsızlaştırır.

```python
from kvkk_maskeleme import incele

rapor = incele(metin)
rapor.var_mi          # True
rapor.kategoriler()   # {"CEZA_MAHKUMIYETI", "SAGLIK"}
print(rapor.uyari())
```

```
Bu belge özel nitelikli kişisel veri içeriyor olabilir
(CEZA_MAHKUMIYETI, DERNEK_VAKIF_SENDIKA, SAGLIK). KVKK md. 6 uyarınca
işlenmesi açık rıza veya kanunda öngörülen bir hâle bağlıdır.
Maskeleme bu veriyi kaldırmaz.
```

Kategoriler kanundaki sırayla ve kanun terminolojisiyle adlandırıldı;
uyum çalışması yapan biri çıktıyı doğrudan maddeye eşleyebilsin diye.

**Hata dengesi burada terstir.** Tanımlayıcı katmanında yanlış pozitif
kötüdür; burada yanlış negatif kötüdür. Boşuna işaretlenen belge bir
insanın birkaç dakikasına mal olur, kaçan belge KVKK ihlaline. Sözlük
katmanı bu yüzden bilerek cömert.

Sağlayıcı verilirse model katmanı da çalışır ve sözlüğün kaçırdığı
bağlamsal ifadeleri ekler.

### Yeniden tanımlanma

Doğrudan tanımlayıcılar kaldırılsa bile bir belge kişiyi
tanımlayabilir: dava türü, tarih, mahkeme ve olayın kendine özgü
ayrıntıları birleşince kimlik ortaya çıkabilir. KVKK'nın tanımı
"kimliği belirli **veya belirlenebilir**" diyor. Bu araç belirlenebilir
olma riskini ölçmüyor.

## Kurulum

```bash
git clone https://github.com/parttimegod/kvkk-maskeleme
cd kvkk-maskeleme
uv sync
```

Bağımlılığı yok; yalnızca standart kütüphane.

## Komut satırı

```bash
kvkk-maskeleme dosya.txt                 # maskele, stdout'a yaz
kvkk-maskeleme dosya.txt -o temiz.txt
cat dosya.txt | kvkk-maskeleme
kvkk-maskeleme dosya.txt --sadece-incele # yalnızca özel nitelikli raporu
kvkk-maskeleme dosya.txt --json
```

Uyarılar ve özet **stderr**'e gider, çıktı stdout'a. Böylece
`kvkk-maskeleme dosya.txt > temiz.txt` yazan biri uyarıyı görür ama
dosyası kirlenmez.

Eşleme tablosu **istenmedikçe yazılmaz** — bütün kişisel veriyi düz
metin içerdiği için maskelenmiş çıktının yanına sessizce bırakılması
maskelemeyi anlamsız kılar:

```bash
kvkk-maskeleme dosya.txt --esleme harita.json
# UYARI: harita.json bütün kişisel veriyi düz metin içeriyor.
```

Çıkış kodları betikler için: `0` temiz, `1` hata, `2` özel nitelikli
veri bulundu (`--kati` ile).

```bash
kvkk-maskeleme dosya.txt --kati > temiz.txt || echo "elle inceleme gerekiyor"
```

## Kullanım

```python
from kvkk_maskeleme import maskele, geri_al

sonuc = maskele(metin)

sonuc.metin      # maskelenmiş metin
sonuc.eslesme    # {"<TC_1>": "12345678901", ...}
sonuc.ozet()     # {"TC": 2, "IBAN": 1}

geri_al(sonuc.metin, sonuc.eslesme)   # özgün metin
```

Örnek çıktı (sentetik belge):

```
DAVACI     : Hatice Özdemir (T.C. Kimlik No: <TC_1>)
ADRES      : Bahçelievler Mahallesi 34. Sokak No: 36/8 İstanbul
TELEFON    : <TELEFON_1>

DAVALI     : Murat Arslan (T.C. Kimlik No: <TC_2>)

AÇIKLAMALAR: Müvekkilim Hatice Özdemir, davalıdan olan alacağını
<IBAN_1> numaralı hesabına havale yoluyla talep etmiş...
```

Kimlik numaraları, telefon ve IBAN maskelendi. **İsimler ve adres
duruyor** — Aşama 2 bunun için.

## Tasarım

**Desen tek başına yetmiyor.** "11 haneli sayı" deseni dosya
numarasını, tutarı, tarih dizisini de yakalar. TC kimlik, VKN, IBAN ve
kart numarasının kontrol hanesi var; doğrulanmayan aday eleniyor.
Yanlış pozitif bu sayede pratikte sıfır.

**Yer tutucular tutarlı.** Aynı numara metinde üç kez geçiyorsa
üçünde de `<TC_1>` yazıyor, farklı numaralar farklı numara alıyor.
Maskelenmiş metin okunabilir kalıyor ve "aynı kişi mi" sorusu
cevaplanabiliyor.

**Çıktı tekrar taranıyor.** Maskeleme bittikten sonra metin yeniden
tespit katmanından geçiyor. Bir şey kaldıysa `SizintiHatasi` fırlıyor.
Sessiz sızıntı, sızıntının kendisinden kötü:

```python
maskele(metin)                  # kirli çıktı olursa hata verir
maskele(metin, dogrula=False)   # yalnızca test içindir
```

**Geri döndürülebilir.** Eşleme tablosu yerelde kalıyor, işlem
zincirinden sonra metin eski haline dönebiliyor. Eşleme tablosu kişisel
veri içerir; metinle birlikte hiçbir yere gönderilmemeli.

## Model katmanı

İsim ve adres desenle bulunamıyor. Türkçe adların bir kısmı günlük
kelimeyle çakışıyor — *Deniz, Umut, Şafak, Barış, Güneş* — yani "büyük
harfle başlayan kelime" kuralı hem kaçırıyor hem yanlış yakalıyor.

```python
from kvkk_maskeleme import maskele, OllamaSaglayici

sonuc = maskele(metin, saglayici=OllamaSaglayici(model="gemma4-abl-16k"))
sonuc.uydurma              # modelin metinde olmayan ifadeleri
sonuc.model_bicim_hatasi   # cevap JSON değilse
```

Sağlayıcı verilmezse yalnızca desen katmanı çalışır. Arayüz tek metotluk
bir protokol, başka bir sunucuya bağlamak kolay.

**Modelden konum istemiyoruz, metin istiyoruz.** Modeller karakter
saymayı beceremiyor; "45. karakterden 56'ya" dediğinde çoğu zaman
yanlış oluyor. Bulduğu ifadeyi aynen yazmasını istiyoruz, konumu biz
buluyoruz. Yan faydası: metinde geçmeyen bir ifade dönerse uydurma
olduğu anlaşılıyor ve sayılıyor.

Çakışmada desen kazanıyor — kontrol hanesiyle doğrulanmış bir kimlik
numarası, modelin "bu bir ad" tahmininden güvenilir.

## Ölçüm

Bu alandaki açık kaynak projelerin hiçbiri ne kadar iyi çalıştığını
söylemiyor. "Kişisel verileri maskeler" cümlesi ölçülmeden bir şey ifade
etmiyor; %60 recall'la çalışan bir araç çalışmıyor demektir.

Sentetik belgeler etiketli olduğu için gerçek recall hesaplanabiliyor.
Ayrıca kişisel veri içermeyen adliye cümlelerinden oluşan bir küme var;
sözlük katmanı onlardan birini işaretlerse yanlış pozitif sayılıyor.

```python
from kvkk_maskeleme.olcum import calistir
print(calistir(20).tablo())
```

```
TANIMLAYICILAR (maskeleniyor)
tür                     beklenen  bulunan   recall
--------------------------------------------------
IBAN                          20       20  100.0%
PLAKA                         20       20  100.0%
TC                            60       60  100.0%
TELEFON                       40       40  100.0%
VKN                           20       20  100.0%

ÖZEL NİTELİKLİ (işaretleniyor)
tür                     beklenen  bulunan   recall
--------------------------------------------------
CEZA_MAHKUMIYETI              20       20  100.0%
DERNEK_VAKIF_SENDIKA          20       20  100.0%
SAGLIK                        20       20  100.0%

belge: 80
temiz metin: 15, yanlış pozitif: 0 (0.0% belgede)
```

Son satır cömert sözlüğün bedelini ölçüyor. Temiz cümleler bilinen
tuzakları barındırıyor: *"tanık dinlenmesi"*, *"Aydın ili"*, *"dinlenme
salonu"*. Bunlar işaretlenirse araç adliyede kullanılamaz hale gelir.

Sağlayıcı verilmediğinde isim ve adres ölçüme katılmıyor; desen
katmanının onları bulması zaten beklenmiyor, ölçüme katmak sonucu
haksız yere düşürür.

## Test verisi

Gerçek belgeyle test edilemez — kişisel veri içeren bir metni geliştirme
sırasında kullanmak, aracın önlemeye çalıştığı ihlalin kendisi olur.
`sentetik.py` etiketli belge üretiyor: hangi kişisel verinin metinde
nerede olduğu biliniyor, bu sayede tespit oranı ölçülebiliyor.

```python
from kvkk_maskeleme.sentetik import dilekce

belge = dilekce(tohum=0)
belge.metin        # sentetik dilekçe
belge.etiketler    # [Etiket("TC", 45, 56, "..."), ...]
```

Üretilen kimlik numaraları kontrol hanesi bakımından geçerlidir, yani
tespit mantığını gerçekten sınarlar. Kimseyi temsil etmezler.

## Testler

```bash
uv run pytest
uv run ruff check .
```

## Lisans

MIT
