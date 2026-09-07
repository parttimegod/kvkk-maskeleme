# turkish-anonymizer

Türkçe metinlerde kişisel veri tespiti ve maskeleme. KVKK kapsamındaki
belgeleri işlemeden önce, özellikle bulut tabanlı bir modele göndermeden
önce kullanılmak üzere.

## Durum

Aşama 1 tamam: yapısal kimlikler. **İsim ve adres henüz yok** — desenle
bulunamıyorlar, yerel model katmanı gerekiyor. Aşağıdaki örnekte bu
eksik açıkça görünüyor.

| Tür | Durum | Yöntem |
|---|---|---|
| TC kimlik no | ✓ | desen + kontrol hanesi |
| Vergi kimlik no | ✓ | desen + kontrol hanesi |
| IBAN | ✓ | desen + mod-97 |
| Kart numarası | ✓ | desen + Luhn |
| Telefon | ✓ | desen |
| Plaka | ✓ | desen |
| E-posta | ✓ | desen |
| **İsim** | ✗ | model katmanı gerekiyor |
| **Adres** | ✗ | model katmanı gerekiyor |

## Kurulum

```bash
git clone https://github.com/parttimegod/turkish-anonymizer
cd turkish-anonymizer
uv sync
```

Bağımlılığı yok; yalnızca standart kütüphane.

## Kullanım

```python
from turkish_anonymizer import maskele, geri_al

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

## Test verisi

Gerçek belgeyle test edilemez — kişisel veri içeren bir metni geliştirme
sırasında kullanmak, aracın önlemeye çalıştığı ihlalin kendisi olur.
`sentetik.py` etiketli belge üretiyor: hangi kişisel verinin metinde
nerede olduğu biliniyor, bu sayede tespit oranı ölçülebiliyor.

```python
from turkish_anonymizer.sentetik import dilekce

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
