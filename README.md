# 🚗 OTO GALERİ YÖNETİM SİSTEMİ
## Veritabanı Tabanlı Araç Alım-Satım Platformu

---

## 📋 İÇİNDEKİLER
1. [Sistem Özellikleri](#sistem-özellikleri)
2. [Kurulum Adımları](#kurulum-adımları)
3. [Veritabanı Kurulumu](#veritabanı-kurulumu)
4. [Çalıştırma](#çalıştırma)
5. [Demo Hesaplar](#demo-hesaplar)
6. [Sayfa Yapısı](#sayfa-yapısı)
7. [Veritabanı Tabloları](#veritabanı-tabloları)

---

## 🎯 SİSTEM ÖZELLİKLERİ

### ✅ ADMIN PANELİ
- ✔️ Bayileri görüntüleme ve yönetme
- ✔️ Tüm araçları listeleme
- ✔️ Kullanıcıları yönetme (admin, personel, müşteri)
- ✔️ Alım ve satım taleplerini görüntüleme
- ✔️ İstatistikler ve raporlar

### ✅ BAYİ PANELİ (Personel)
- ✔️ Kendi bayisinin araçlarını görüntüleme
- ✔️ Yeni araç ekleme (marka, model, yıl, km, yakıt, vites, renk, fiyat, plaka)
- ✔️ Müşterilerden gelen ALIM taleplerini görme ve yönetme
- ✔️ Müşterilerden gelen SATIM taleplerini görme ve yönetme
- ✔️ Talep durumlarını güncelleme (Beklemede, Görüşülüyor, Onaylandı, İptal)

### ✅ MÜŞTERİ PANELİ
- ✔️ Satışta olan araçları görüntüleme
- ✔️ Araçlar için alım talebi oluşturma
- ✔️ Kendi taleplerini takip etme
- ✔️ Talep geçmişini görüntüleme

---

## 🛠️ KURULUM ADIMLARI

### 1️⃣ XAMPP Kurulumu
1. XAMPP'i indir ve kur: https://www.apachefriends.org/
2. XAMPP Control Panel'i aç
3. **Apache** ve **MySQL** servislerini başlat

### 2️⃣ Python Kütüphanelerini Kur
```bash
# Terminal veya CMD'de proje klasöründe çalıştır:
pip install -r requirements.txt
```

**requirements.txt içeriği:**
```
Flask==3.0.0
mysql-connector-python==8.2.0
Werkzeug==3.0.1
```

---

## 🗄️ VERİTABANI KURULUMU

### 1️⃣ phpMyAdmin'e Giriş
1. Tarayıcıda aç: `http://localhost/phpmyadmin`
2. Sol tarafta **Yeni (New)** butonuna tıkla

### 2️⃣ Veritabanı Oluştur
1. Veritabanı adı: `oto_galeri`
2. Karakter seti: `utf8mb4_general_ci`
3. **Oluştur** butonuna tıkla

### 3️⃣ SQL Dosyasını İçe Aktar
1. `oto_galeri` veritabanına tıkla
2. Üstteki **SQL** sekmesine tıkla
3. Aşağıdaki SQL kodunu yapıştır ve **Çalıştır** butonuna tıkla:

```sql
-- =====================================
-- KULLANICILAR
-- =====================================

CREATE TABLE kullanicilar (
    kullanici_id INT PRIMARY KEY AUTO_INCREMENT,
    ad VARCHAR(50),
    soyad VARCHAR(50),
    email VARCHAR(100),
    telefon VARCHAR(20),
    sifre VARCHAR(100),
    yetki VARCHAR(20),
    kayit_tarihi DATETIME
);

INSERT INTO kullanicilar 
(ad, soyad, email, telefon, sifre, yetki, kayit_tarihi)
VALUES
('Ahmet', 'Yilmaz', 'ahmet@gmail.com', '05551111111', '123', 'musteri', NOW()),
('Mehmet', 'Demir', 'mehmet@gmail.com', '05552222222', '123', 'personel', NOW()),
('Ayse', 'Kaya', 'ayse@gmail.com', '05553333333', '123', 'admin', NOW());

-- =====================================
-- BAYILER
-- =====================================

CREATE TABLE bayiler (
    bayi_id INT PRIMARY KEY AUTO_INCREMENT,
    bayi_adi VARCHAR(100),
    adres TEXT,
    sehir VARCHAR(50),
    telefon VARCHAR(20),
    email VARCHAR(100)
);

INSERT INTO bayiler
(bayi_adi, adres, sehir, telefon, email)
VALUES
('Diyarbakir Oto', 'Baglar Mahallesi', 'Diyarbakir', '04120000001', 'diyarbakir@oto.com'),
('Elazig Motor', 'Merkez', 'Elazig', '04120000002', 'elazig@oto.com'),
('Mardin Galeri', 'Artuklu', 'Mardin', '04120000003', 'mardin@oto.com');

-- =====================================
-- PERSONELLER
-- =====================================

CREATE TABLE personeller (
    personel_id INT PRIMARY KEY AUTO_INCREMENT,
    kullanici_id INT,
    bayi_id INT,
    gorev VARCHAR(50),
    ise_giris_tarihi DATE,

    FOREIGN KEY (kullanici_id)
    REFERENCES kullanicilar(kullanici_id),

    FOREIGN KEY (bayi_id)
    REFERENCES bayiler(bayi_id)
);

INSERT INTO personeller
(kullanici_id, bayi_id, gorev, ise_giris_tarihi)
VALUES
(2, 1, 'Satis Danismani', '2025-01-10');

-- =====================================
-- ARACLAR
-- =====================================

CREATE TABLE araclar (
    arac_id INT PRIMARY KEY AUTO_INCREMENT,
    bayi_id INT,

    marka VARCHAR(50),
    model VARCHAR(50),
    yil INT,
    kilometre INT,

    yakit VARCHAR(30),
    vites VARCHAR(30),
    renk VARCHAR(30),

    fiyat DECIMAL(10,2),
    plaka VARCHAR(20),

    arac_durumu VARCHAR(30),
    aciklama TEXT,

    ilan_tarihi DATETIME,

    FOREIGN KEY (bayi_id)
    REFERENCES bayiler(bayi_id)
);

INSERT INTO araclar
(
    bayi_id,
    marka,
    model,
    yil,
    kilometre,
    yakit,
    vites,
    renk,
    fiyat,
    plaka,
    arac_durumu,
    aciklama,
    ilan_tarihi
)
VALUES
(1, 'Renault', 'Clio', 2021, 45000, 'Benzin', 'Manuel', 'Beyaz', 850000, '21 ABC 001', 'Satista', 'Temiz aile araci', NOW()),

(1, 'Toyota', 'Corolla', 2020, 60000, 'Dizel', 'Otomatik', 'Siyah', 1100000, '21 ABC 002', 'Satista', 'Bakimli arac', NOW()),

(2, 'BMW', '320i', 2019, 80000, 'Benzin', 'Otomatik', 'Gri', 1850000, '23 ABC 003', 'Rezerve', 'Full paket', NOW());

-- =====================================
-- ARAC ALIM TALEBI
-- =====================================

CREATE TABLE arac_alim_talebi (
    talep_id INT PRIMARY KEY AUTO_INCREMENT,

    musteri_id INT,
    arac_id INT,

    odeme_tipi VARCHAR(50),
    durum VARCHAR(50),
    notlar TEXT,

    talep_tarihi DATETIME,

    FOREIGN KEY (musteri_id)
    REFERENCES kullanicilar(kullanici_id),

    FOREIGN KEY (arac_id)
    REFERENCES araclar(arac_id)
);

INSERT INTO arac_alim_talebi
(
    musteri_id,
    arac_id,
    odeme_tipi,
    durum,
    notlar,
    talep_tarihi
)
VALUES
(1, 1, 'Kredi', 'Beklemede', 'Araci hafta sonu görmek istiyorum', NOW()),

(1, 2, 'Pesin', 'Gorusuluyor', 'Fiyat konusunda bilgi almak istiyorum', NOW());

-- =====================================
-- ARAC SATIM TALEBI
-- =====================================

CREATE TABLE arac_satim_talebi (
    talep_id INT PRIMARY KEY AUTO_INCREMENT,

    musteri_id INT,
    bayi_id INT,

    marka VARCHAR(50),
    model VARCHAR(50),
    yil INT,
    kilometre INT,

    fiyat_beklentisi DECIMAL(10,2),

    ekspertiz VARCHAR(50),
    durum VARCHAR(50),

    talep_tarihi DATETIME,

    FOREIGN KEY (musteri_id)
    REFERENCES kullanicilar(kullanici_id),

    FOREIGN KEY (bayi_id)
    REFERENCES bayiler(bayi_id)
);

INSERT INTO arac_satim_talebi
(
    musteri_id,
    bayi_id,
    marka,
    model,
    yil,
    kilometre,
    fiyat_beklentisi,
    ekspertiz,
    durum,
    talep_tarihi
)
VALUES
(1, 1, 'Honda', 'Civic', 2018, 95000, 950000, 'Var', 'Beklemede', NOW()),

(1, 2, 'Ford', 'Focus', 2017, 120000, 780000, 'Yok', 'Inceleniyor', NOW());
```

---

## ▶️ ÇALIŞTIRMA

### 1️⃣ Proje Klasörünü Aç
Terminal veya CMD'de proje klasörüne git:
```bash
cd C:\Users\KullaniciAdin\Desktop\oto_galeri
```

### 2️⃣ Flask Uygulamasını Başlat
```bash
python app.py
```

### 3️⃣ Tarayıcıda Aç
Tarayıcıda şu adresi aç:
```
http://localhost:5000
```

veya

```
http://127.0.0.1:5000
```

---

## 👥 DEMO HESAPLAR

### 👑 Admin Hesabı
- **Email:** ayse@gmail.com
- **Şifre:** 123
- **Yetkiler:** Tüm sistemi yönetebilir

### 👨‍💼 Personel Hesabı (Bayi)
- **Email:** mehmet@gmail.com
- **Şifre:** 123
- **Bayi:** Diyarbakir Oto
- **Yetkiler:** Kendi bayisinin araçlarını ve taleplerini yönetir

### 🙋 Müşteri Hesabı
- **Email:** ahmet@gmail.com
- **Şifre:** 123
- **Yetkiler:** Araç satın alabilir, talep oluşturabilir

---

## 📁 SAYFA YAPISI

### 🗂️ Klasör Yapısı
```
oto_galeri/
│
├── app.py                          # Flask ana uygulama
├── config.py                       # Ayarlar dosyası
├── requirements.txt                # Python kütüphaneleri
│
├── static/
│   └── style.css                   # Tüm CSS stilleri
│
└── templates/
    ├── login.html                  # Giriş sayfası
    ├── kayit.html                  # Kayıt sayfası
    │
    ├── admin/
    │   ├── index.html              # Admin ana sayfa
    │   ├── bayiler.html            # Bayiler listesi
    │   ├── araclar.html            # Araçlar listesi
    │   ├── kullanicilar.html       # Kullanıcılar listesi
    │   └── talepler.html           # Talepler listesi
    │
    ├── bayi/
    │   ├── index.html              # Bayi ana sayfa
    │   ├── araclar.html            # Bayi araçları
    │   ├── arac_ekle.html          # Araç ekleme formu
    │   ├── alim_talepleri.html     # Alım talepleri
    │   └── satim_talepleri.html    # Satım talepleri
    │
    └── musteri/
        ├── index.html              # Müşteri ana sayfa
        ├── araclar.html            # Araç listesi
        ├── talep_olustur.html      # Talep oluşturma
        └── taleplerim.html         # Taleplerim
```

---

## 🗃️ VERİTABANI TABLOLARI

### 1️⃣ kullanicilar (Kullanıcı Bilgileri)
- kullanici_id (PK)
- ad, soyad, email, telefon
- sifre
- yetki (admin / personel / musteri)
- kayit_tarihi

### 2️⃣ bayiler (Bayi Bilgileri)
- bayi_id (PK)
- bayi_adi, adres, sehir
- telefon, email

### 3️⃣ personeller (Personel-Bayi İlişkisi)
- personel_id (PK)
- kullanici_id (FK → kullanicilar)
- bayi_id (FK → bayiler)
- gorev, ise_giris_tarihi

### 4️⃣ araclar (Araç Bilgileri)
- arac_id (PK)
- bayi_id (FK → bayiler)
- marka, model, yil, kilometre
- yakit, vites, renk
- fiyat, plaka
- arac_durumu (Satista / Rezerve / Satildi)
- aciklama, ilan_tarihi

### 5️⃣ arac_alim_talebi (Müşteri Alım Talepleri)
- talep_id (PK)
- musteri_id (FK → kullanicilar)
- arac_id (FK → araclar)
- odeme_tipi (Pesin / Kredi / Takas)
- durum (Beklemede / Gorusuluyor / Onaylandi)
- notlar, talep_tarihi

### 6️⃣ arac_satim_talebi (Müşteri Satım Talepleri)
- talep_id (PK)
- musteri_id (FK → kullanicilar)
- bayi_id (FK → bayiler)
- marka, model, yil, kilometre
- fiyat_beklentisi
- ekspertiz (Var / Yok)
- durum (Beklemede / Inceleniyor / Teklif Verildi)
- talep_tarihi

---

## 🔗 İLİŞKİ DIYAGRAMI

```
kullanicilar (1) ----< (N) personeller
bayiler (1) ----< (N) personeller
bayiler (1) ----< (N) araclar
kullanicilar (1) ----< (N) arac_alim_talebi
araclar (1) ----< (N) arac_alim_talebi
kullanicilar (1) ----< (N) arac_satim_talebi
bayiler (1) ----< (N) arac_satim_talebi
```

---

## 🎓 PROJE HAKKINDA

Bu proje **Veritabanı Tasarımı** dersi için hazırlanmış bir oto galeri yönetim sistemidir.

### Öğrenilen Konular:
✅ MySQL veritabanı tasarımı
✅ Tablo ilişkileri (Foreign Key)
✅ Flask web framework
✅ HTML/CSS/JavaScript
✅ CRUD işlemleri (Create, Read, Update, Delete)
✅ Session yönetimi
✅ Kullanıcı yetkilendirme

---

## ⚠️ SORUN GİDERME

### Hata: "ModuleNotFoundError: No module named 'flask'"
**Çözüm:**
```bash
pip install Flask mysql-connector-python
```

### Hata: "Can't connect to MySQL server"
**Çözüm:**
1. XAMPP Control Panel'de MySQL'in çalıştığından emin olun
2. phpMyAdmin'e giriş yapabildiğinizi kontrol edin

### Hata: "Table 'oto_galeri.kullanicilar' doesn't exist"
**Çözüm:**
1. phpMyAdmin'e gidin
2. SQL dosyasını tekrar çalıştırın

---

## 📞 İLETİŞİM

Sorularınız için:
- Proje sahibi ile iletişime geçin
- README dosyasını dikkatle okuyun

---

## 🎉 BAŞARILAR!

Projenizi başarıyla kurdunuz! 🚀
Şimdi sistemi kullanarak araç alım-satım işlemlerini yönetebilirsiniz.

**Kolay gelsin! 💪**