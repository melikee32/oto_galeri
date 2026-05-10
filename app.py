from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

# Uygulamayı başlat
uygulama = Flask(__name__)
uygulama.secret_key = 'gizli123'

# --------------------------------------------------
# Veritabanına bağlan
# --------------------------------------------------
def baglan():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='oto_galeri'
    )

# --------------------------------------------------
# Ana sayfa - kullanıcıya göre yönlendir
# --------------------------------------------------
@uygulama.route('/')
def anasayfa():
    if 'id' not in session:
        return redirect(url_for('giris'))
    if session['yetki'] == 'admin':
        return redirect(url_for('admin_panel'))
    elif session['yetki'] == 'personel':
        return redirect(url_for('bayi_panel'))
    else:
        return redirect(url_for('musteri_panel'))

# --------------------------------------------------
# GİRİŞ
# --------------------------------------------------
@uygulama.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        email = request.form['email']
        sifre = request.form['sifre']

        db = baglan()
        im = db.cursor(dictionary=True)
        im.execute("SELECT * FROM kullanicilar WHERE email=%s AND sifre=%s", (email, sifre))
        kul = im.fetchone()
        im.close()
        db.close()

        if kul:
            # Kullanıcı bilgilerini session'a kaydet
            session['id']       = kul['kullanici_id']
            session['ad_soyad'] = kul['ad_soyad']
            session['email']    = kul['email']
            session['telefon']  = kul['telefon']
            session['yetki']    = kul['yetki']
            flash('Giris basarili!', 'success')

            if kul['yetki'] == 'admin':
                return redirect(url_for('admin_panel'))
            elif kul['yetki'] == 'personel':
                return redirect(url_for('bayi_panel'))
            else:
                return redirect(url_for('musteri_panel'))
        else:
            flash('Email veya sifre yanlis!', 'error')

    return render_template('giris.html')

# --------------------------------------------------
# ÇIKIŞ
# --------------------------------------------------
@uygulama.route('/cikis')
def cikis():
    session.clear()
    return redirect(url_for('giris'))

# --------------------------------------------------
# KAYIT (sadece müşteri)
# --------------------------------------------------
@uygulama.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        ad_soyad = request.form['ad_soyad'][:50]
        email    = request.form['email'][:100]
        telefon  = request.form['telefon'][:11]
        sifre    = request.form['sifre'][:20]

        db = baglan()
        im = db.cursor()
        try:
            im.execute("""INSERT INTO kullanicilar (ad_soyad, email, telefon, sifre, yetki)
                          VALUES (%s, %s, %s, %s, 'musteri')""",
                       (ad_soyad, email, telefon, sifre))
            db.commit()
            flash('Kayit basarili! Giris yapabilirsiniz.', 'success')
            return redirect(url_for('giris'))
        except:
            flash('Bu email zaten kullaniliyor!', 'error')
        finally:
            im.close()
            db.close()

    return render_template('kayit.html')

# --------------------------------------------------
# ADMİN PANELİ
# --------------------------------------------------
@uygulama.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'id' not in session or session['yetki'] != 'admin':
        return redirect(url_for('giris'))

    db = baglan()
    im = db.cursor(dictionary=True)

    # Yeni bayi ekle
    if request.method == 'POST' and 'bayi_ekle' in request.form:
        try:
            # Önce bayiyi ekle
            im.execute("""INSERT INTO bayiler (bayi_adi, sehir, adres, telefon, email)
                          VALUES (%s, %s, %s, %s, %s)""",
                       (request.form['bayi_adi'][:50], request.form['sehir'][:30],
                        request.form['adres'][:100],   request.form['b_telefon'][:11],
                        request.form['b_email'][:100]))
            yeni_bayi_id = im.lastrowid

            # Sonra bayinin kullanıcı hesabını ekle
            im.execute("""INSERT INTO kullanicilar (ad_soyad, email, telefon, sifre, yetki)
                          VALUES (%s, %s, %s, %s, 'personel')""",
                       (request.form['ad_soyad'][:50],  request.form['k_email'][:100],
                        request.form['k_telefon'][:11], request.form['k_sifre'][:20]))
            yeni_kul_id = im.lastrowid

            # Kullanıcıyı bayiye bağla
            im.execute("""INSERT INTO personeller (kullanici_id, bayi_id, gorev)
                          VALUES (%s, %s, 'Yetkili')""", (yeni_kul_id, yeni_bayi_id))
            db.commit()
            flash('Bayi eklendi!', 'success')
        except Exception as h:
            flash('Hata: ' + str(h), 'error')

    # Bayi sil
    if request.method == 'POST' and 'bayi_sil' in request.form:
        bid = request.form['bayi_id']
        im.execute("DELETE FROM arac_alim_talebi WHERE arac_id IN (SELECT arac_id FROM araclar WHERE bayi_id=%s)", (bid,))
        im.execute("DELETE FROM arac_satim_talebi WHERE bayi_id=%s", (bid,))
        im.execute("DELETE FROM araclar WHERE bayi_id=%s", (bid,))
        im.execute("SELECT kullanici_id FROM personeller WHERE bayi_id=%s", (bid,))
        personeller = im.fetchall()
        im.execute("DELETE FROM personeller WHERE bayi_id=%s", (bid,))
        for p in personeller:
            im.execute("DELETE FROM kullanicilar WHERE kullanici_id=%s", (p['kullanici_id'],))
        im.execute("DELETE FROM bayiler WHERE bayi_id=%s", (bid,))
        db.commit()
        flash('Bayi silindi!', 'success')

    # Kullanıcı sil
    if request.method == 'POST' and 'kullanici_sil' in request.form:
        kid = request.form['kullanici_id']
        im.execute("DELETE FROM arac_alim_talebi WHERE musteri_id=%s", (kid,))
        im.execute("DELETE FROM arac_satim_talebi WHERE musteri_id=%s", (kid,))
        im.execute("DELETE FROM personeller WHERE kullanici_id=%s", (kid,))
        im.execute("DELETE FROM kullanicilar WHERE kullanici_id=%s", (kid,))
        db.commit()
        flash('Kullanici silindi!', 'success')

    # Araç sil
    if request.method == 'POST' and 'arac_sil' in request.form:
        aid = request.form['arac_id']
        im.execute("DELETE FROM arac_alim_talebi WHERE arac_id=%s", (aid,))
        im.execute("DELETE FROM araclar WHERE arac_id=%s", (aid,))
        db.commit()
        flash('Arac silindi!', 'success')

    # Verileri çek
    im.execute("SELECT b.*, COUNT(a.arac_id) as arac_sayisi FROM bayiler b LEFT JOIN araclar a ON b.bayi_id=a.bayi_id GROUP BY b.bayi_id")
    bayiler = im.fetchall()

    im.execute("SELECT a.*, b.bayi_adi FROM araclar a JOIN bayiler b ON a.bayi_id=b.bayi_id")
    araclar = im.fetchall()

    im.execute("SELECT * FROM kullanicilar")
    kullanicilar = im.fetchall()

    im.execute("""SELECT t.*, a.marka, a.model, a.fiyat, b.bayi_adi, k.ad_soyad
                  FROM arac_alim_talebi t
                  JOIN araclar a ON t.arac_id=a.arac_id
                  JOIN bayiler b ON a.bayi_id=b.bayi_id
                  JOIN kullanicilar k ON t.musteri_id=k.kullanici_id
                  ORDER BY t.talep_tarihi DESC""")
    alim_talepleri = im.fetchall()

    im.execute("""SELECT t.*, b.bayi_adi, k.ad_soyad
                  FROM arac_satim_talebi t
                  JOIN bayiler b ON t.bayi_id=b.bayi_id
                  JOIN kullanicilar k ON t.musteri_id=k.kullanici_id
                  ORDER BY t.talep_tarihi DESC""")
    satim_talepleri = im.fetchall()

    im.close()
    db.close()

    return render_template('admin.html',
                           bayiler=bayiler, araclar=araclar,
                           kullanicilar=kullanicilar,
                           alim_talepleri=alim_talepleri,
                           satim_talepleri=satim_talepleri)

# --------------------------------------------------
# BAYİ PANELİ
# --------------------------------------------------
@uygulama.route('/bayi', methods=['GET', 'POST'])
def bayi_panel():
    if 'id' not in session or session['yetki'] != 'personel':
        return redirect(url_for('giris'))

    db = baglan()
    im = db.cursor(dictionary=True)

    # Bu kullanıcının bayisini bul
    im.execute("SELECT bayi_id FROM personeller WHERE kullanici_id=%s", (session['id'],))
    sonuc = im.fetchone()
    if not sonuc:
        return redirect(url_for('cikis'))
    bayi_id = sonuc['bayi_id']

    # Araç ekle
    if request.method == 'POST' and 'arac_ekle' in request.form:
        im.execute("""INSERT INTO araclar (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, fiyat, plaka, arac_durumu)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Satista')""",
                   (bayi_id,
                    request.form['marka'][:30],    request.form['model'][:30],
                    request.form['yil'],            request.form['kilometre'],
                    request.form['yakit'],          request.form['vites'],
                    request.form['renk'][:15],      request.form['fiyat'],
                    request.form['plaka'][:10]))
        db.commit()
        flash('Arac eklendi!', 'success')

    # Araç sil
    if request.method == 'POST' and 'arac_sil' in request.form:
        aid = request.form['arac_id']
        im.execute("DELETE FROM arac_alim_talebi WHERE arac_id=%s", (aid,))
        im.execute("DELETE FROM araclar WHERE arac_id=%s AND bayi_id=%s", (aid, bayi_id))
        db.commit()
        flash('Arac silindi!', 'success')

    # Alım talebi durumunu güncelle
    if request.method == 'POST' and 'alim_guncelle' in request.form:
        yeni_durum = request.form['durum']
        alim_id    = request.form['alim_id']
        arac_id    = request.form['arac_id']
        im.execute("UPDATE arac_alim_talebi SET durum=%s WHERE alim_id=%s", (yeni_durum, alim_id))
        # Onaylandıysa aracı satıldı olarak işaretle
        if yeni_durum == 'Onaylandi':
            im.execute("UPDATE araclar SET arac_durumu='Satildi' WHERE arac_id=%s", (arac_id,))
        db.commit()
        flash('Talep guncellendi!', 'success')

    # Satım talebi durumunu güncelle
    if request.method == 'POST' and 'satim_guncelle' in request.form:
        yeni_durum = request.form['durum']
        satim_id   = request.form['satim_id']
        im.execute("UPDATE arac_satim_talebi SET durum=%s WHERE satim_id=%s", (yeni_durum, satim_id))
        # Satin alindiysa araci stoga ekle
        if yeni_durum == 'Satin Alindi':
            im.execute("SELECT * FROM arac_satim_talebi WHERE satim_id=%s", (satim_id,))
            talep = im.fetchone()
            im.execute("""INSERT INTO araclar (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, fiyat, plaka, arac_durumu)
                          VALUES (%s, %s, %s, %s, %s, 'Benzin', 'Manuel', '-', %s, '-', 'Satista')""",
                       (bayi_id, talep['marka'], talep['model'], talep['yil'],
                        talep['kilometre'], talep['fiyat_beklentisi']))
        db.commit()
        flash('Talep guncellendi!', 'success')

    # Personel ekle
    if request.method == 'POST' and 'personel_ekle' in request.form:
        try:
            im.execute("""INSERT INTO kullanicilar (ad_soyad, email, telefon, sifre, yetki)
                          VALUES (%s, %s, %s, %s, 'personel')""",
                       (request.form['p_ad_soyad'][:50], request.form['p_email'][:100],
                        request.form['p_telefon'][:11],  request.form['p_sifre'][:20]))
            db.commit()
            yeni_id = im.lastrowid
            im.execute("INSERT INTO personeller (kullanici_id, bayi_id, gorev) VALUES (%s, %s, %s)",
                       (yeni_id, bayi_id, request.form['p_gorev'][:30]))
            db.commit()
            flash('Personel eklendi!', 'success')
        except Exception as h:
            flash('Hata: ' + str(h), 'error')

    # Verileri çek
    im.execute("SELECT * FROM bayiler WHERE bayi_id=%s", (bayi_id,))
    bayi = im.fetchone()

    im.execute("SELECT * FROM araclar WHERE bayi_id=%s", (bayi_id,))
    araclar = im.fetchall()

    # Bayinin personellerini getir
    im.execute("""SELECT k.kullanici_id, k.ad_soyad, k.email, k.telefon, p.gorev, p.personel_id
                  FROM personeller p
                  JOIN kullanicilar k ON p.kullanici_id=k.kullanici_id
                  WHERE p.bayi_id=%s""", (bayi_id,))
    personeller = im.fetchall()

    im.execute("""SELECT t.*, a.marka, a.model, a.fiyat, k.ad_soyad, k.telefon
                  FROM arac_alim_talebi t
                  JOIN araclar a ON t.arac_id=a.arac_id
                  JOIN kullanicilar k ON t.musteri_id=k.kullanici_id
                  WHERE a.bayi_id=%s ORDER BY t.talep_tarihi DESC""", (bayi_id,))
    alim_talepleri = im.fetchall()

    im.execute("""SELECT t.*, k.ad_soyad, k.telefon
                  FROM arac_satim_talebi t
                  JOIN kullanicilar k ON t.musteri_id=k.kullanici_id
                  WHERE t.bayi_id=%s ORDER BY t.talep_tarihi DESC""", (bayi_id,))
    satim_talepleri = im.fetchall()

    im.close()
    db.close()

    return render_template('bayi.html',
                           bayi=bayi, araclar=araclar,
                           personeller=personeller,
                           alim_talepleri=alim_talepleri,
                           satim_talepleri=satim_talepleri)

# --------------------------------------------------
# MÜŞTERİ PANELİ
# --------------------------------------------------
@uygulama.route('/musteri', methods=['GET', 'POST'])
def musteri_panel():
    if 'id' not in session or session['yetki'] != 'musteri':
        return redirect(url_for('giris'))

    db = baglan()
    im = db.cursor(dictionary=True)

    # Alım talebi gönder
    if request.method == 'POST' and 'alim_talep' in request.form:
        im.execute("""INSERT INTO arac_alim_talebi (musteri_id, arac_id, odeme_tipi, durum, talep_tarihi)
                      VALUES (%s, %s, %s, 'Beklemede', NOW())""",
                   (session['id'], request.form['arac_id'], request.form['odeme_tipi']))
        db.commit()
        flash('Alim talebi gonderildi!', 'success')

    # Satım talebi gönder
    if request.method == 'POST' and 'satim_talep' in request.form:
        im.execute("""INSERT INTO arac_satim_talebi 
                      (musteri_id, bayi_id, marka, model, yil, kilometre, fiyat_beklentisi, ekspertiz, durum, talep_tarihi)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Beklemede',NOW())""",
                   (session['id'],              request.form['bayi_id'],
                    request.form['marka'][:30], request.form['model'][:30],
                    request.form['yil'],         request.form['kilometre'],
                    request.form['fiyat'],       request.form['ekspertiz']))
        db.commit()
        flash('Satim talebi gonderildi!', 'success')

    # Satilik araçları getir
    im.execute("""SELECT a.*, b.bayi_adi, b.sehir FROM araclar a
                  JOIN bayiler b ON a.bayi_id=b.bayi_id
                  WHERE a.arac_durumu='Satista'""")
    araclar = im.fetchall()

    # Tüm bayileri getir
    im.execute("SELECT * FROM bayiler")
    bayiler = im.fetchall()

    # Müşterinin alım taleplerini getir
    im.execute("""SELECT t.*, a.marka, a.model, a.fiyat, b.bayi_adi
                  FROM arac_alim_talebi t
                  JOIN araclar a ON t.arac_id=a.arac_id
                  JOIN bayiler b ON a.bayi_id=b.bayi_id
                  WHERE t.musteri_id=%s ORDER BY t.talep_tarihi DESC""", (session['id'],))
    alim_taleplerim = im.fetchall()

    # Müşterinin satım taleplerini getir
    im.execute("""SELECT t.*, b.bayi_adi FROM arac_satim_talebi t
                  JOIN bayiler b ON t.bayi_id=b.bayi_id
                  WHERE t.musteri_id=%s ORDER BY t.talep_tarihi DESC""", (session['id'],))
    satim_taleplerim = im.fetchall()

    im.close()
    db.close()

    return render_template('musteri.html',
                           araclar=araclar, bayiler=bayiler,
                           alim_talepleri=alim_taleplerim,
                           satim_talepleri=satim_taleplerim)


if __name__ == '__main__':
    uygulama.run(debug=True, port=5000)