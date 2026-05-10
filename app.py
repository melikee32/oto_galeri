from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_12345'


def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='oto_galeri'
    )


# ============================================
# ANA SAYFA
# ============================================
@app.route('/')
def index():
    if 'kullanici_id' in session:
        if session['yetki'] == 'admin':
            return redirect(url_for('admin'))
        elif session['yetki'] == 'personel':
            return redirect(url_for('bayi'))
        elif session['yetki'] == 'musteri':
            return redirect(url_for('musteri'))
    return redirect(url_for('login'))


# ============================================
# LOGIN
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        sifre = request.form['sifre']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM kullanicilar WHERE email=%s AND sifre=%s", (email, sifre))
        kullanici = cursor.fetchone()
        cursor.close()
        db.close()

        if kullanici:
            session['kullanici_id'] = kullanici['kullanici_id']
            session['ad'] = kullanici['ad']
            session['soyad'] = kullanici['soyad']
            session['email'] = kullanici['email']
            session['telefon'] = kullanici['telefon']
            session['yetki'] = kullanici['yetki']
            session['kayit_tarihi'] = str(kullanici['kayit_tarihi'])
            flash('Giris basarili!', 'success')

            if kullanici['yetki'] == 'admin':
                return redirect(url_for('admin'))
            elif kullanici['yetki'] == 'personel':
                return redirect(url_for('bayi'))
            else:
                return redirect(url_for('musteri'))
        else:
            flash('Email veya sifre hatali!', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Cikis yapildi!', 'success')
    return redirect(url_for('login'))


# ============================================
# KAYIT - SADECE MUSTERI
# ============================================
@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        email = request.form['email']
        telefon = request.form['telefon']
        sifre = request.form['sifre']

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("""INSERT INTO kullanicilar 
                            (ad, soyad, email, telefon, sifre, yetki, kayit_tarihi)
                            VALUES (%s, %s, %s, %s, %s, 'musteri', NOW())""",
                           (ad, soyad, email, telefon, sifre))
            db.commit()
            cursor.close()
            db.close()
            flash('Kayit basarili! Giris yapabilirsiniz.', 'success')
            return redirect(url_for('login'))
        except:
            cursor.close()
            db.close()
            flash('Bu email zaten kullaniliyor!', 'error')

    return render_template('kayit.html')


# ============================================
# PROFIL GUNCELLE
# ============================================
@app.route('/profil_guncelle', methods=['POST'])
def profil_guncelle():
    if 'kullanici_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    email = request.form.get('profil_email', '')
    telefon = request.form.get('profil_telefon', '')
    yeni_sifre = request.form.get('profil_yeni_sifre', '')
    yeni_sifre_confirm = request.form.get('profil_yeni_sifre_confirm', '')

    if yeni_sifre:
        if yeni_sifre != yeni_sifre_confirm:
            flash('Sifreler eslesmiyor!', 'error')
            cursor.close()
            db.close()
            return redirect(request.referrer)
        cursor.execute("UPDATE kullanicilar SET email=%s, telefon=%s, sifre=%s WHERE kullanici_id=%s",
                       (email, telefon, yeni_sifre, session['kullanici_id']))
    else:
        cursor.execute("UPDATE kullanicilar SET email=%s, telefon=%s WHERE kullanici_id=%s",
                       (email, telefon, session['kullanici_id']))

    db.commit()
    cursor.close()
    db.close()

    session['email'] = email
    session['telefon'] = telefon
    flash('Profil guncellendi!', 'success')
    return redirect(request.referrer)


# ============================================
# ADMIN PANEL
# ============================================
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'kullanici_id' not in session or session['yetki'] != 'admin':
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # BAYI EKLE
    if request.method == 'POST' and 'bayi_ekle' in request.form:
        try:
            cursor.execute("""INSERT INTO bayiler (bayi_adi, sehir, adres, telefon, email)
                            VALUES (%s, %s, %s, %s, %s)""",
                           (request.form['bayi_adi'], request.form['sehir'],
                            request.form.get('adres', ''), request.form['telefon'],
                            request.form['email']))
            yeni_bayi_id = cursor.lastrowid

            cursor.execute("""INSERT INTO kullanicilar 
                            (ad, soyad, email, telefon, sifre, yetki, kayit_tarihi)
                            VALUES (%s, %s, %s, %s, %s, 'personel', NOW())""",
                           (request.form['yetkili_ad'], request.form['yetkili_soyad'],
                            request.form['yetkili_email'], request.form['yetkili_telefon'],
                            request.form['yetkili_sifre']))
            yeni_kullanici_id = cursor.lastrowid

            cursor.execute("""INSERT INTO personeller (kullanici_id, bayi_id, gorev, ise_giris_tarihi)
                            VALUES (%s, %s, 'Yetkili', CURDATE())""",
                           (yeni_kullanici_id, yeni_bayi_id))
            db.commit()
            flash('Bayi ve yetkilisi eklendi!', 'success')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')

    # BAYI GUNCELLE
    if request.method == 'POST' and 'bayi_guncelle' in request.form:
        cursor.execute("""UPDATE bayiler SET bayi_adi=%s, sehir=%s, telefon=%s, email=%s
                         WHERE bayi_id=%s""",
                       (request.form['bayi_adi'], request.form['sehir'],
                        request.form['telefon'], request.form['email'],
                        request.form['bayi_id']))
        db.commit()
        flash('Bayi guncellendi!', 'success')

    # BAYI SIL
    if request.method == 'POST' and 'bayi_sil' in request.form:
        bayi_id = request.form['bayi_id']
        cursor.execute("""DELETE FROM arac_alim_talebi 
                        WHERE arac_id IN (SELECT arac_id FROM araclar WHERE bayi_id=%s)""", (bayi_id,))
        cursor.execute("DELETE FROM arac_satim_talebi WHERE bayi_id=%s", (bayi_id,))
        cursor.execute("DELETE FROM araclar WHERE bayi_id=%s", (bayi_id,))
        cursor.execute("SELECT kullanici_id FROM personeller WHERE bayi_id=%s", (bayi_id,))
        personeller = cursor.fetchall()
        cursor.execute("DELETE FROM personeller WHERE bayi_id=%s", (bayi_id,))
        for p in personeller:
            cursor.execute("DELETE FROM kullanicilar WHERE kullanici_id=%s", (p['kullanici_id'],))
        cursor.execute("DELETE FROM bayiler WHERE bayi_id=%s", (bayi_id,))
        db.commit()
        flash('Bayi silindi!', 'success')

    # KULLANICI SIL
    if request.method == 'POST' and 'kullanici_sil' in request.form:
        kullanici_id = request.form['kullanici_id']
        cursor.execute("DELETE FROM arac_alim_talebi WHERE musteri_id=%s", (kullanici_id,))
        cursor.execute("DELETE FROM arac_satim_talebi WHERE musteri_id=%s", (kullanici_id,))
        cursor.execute("DELETE FROM personeller WHERE kullanici_id=%s", (kullanici_id,))
        cursor.execute("DELETE FROM kullanicilar WHERE kullanici_id=%s", (kullanici_id,))
        db.commit()
        flash('Kullanici silindi!', 'success')

    # KULLANICI GUNCELLE
    if request.method == 'POST' and 'kullanici_guncelle' in request.form:
        cursor.execute("""UPDATE kullanicilar SET ad=%s, soyad=%s, telefon=%s 
                         WHERE kullanici_id=%s""",
                       (request.form['ad'], request.form['soyad'],
                        request.form['telefon'], request.form['kullanici_id']))
        db.commit()
        flash('Kullanici guncellendi!', 'success')

    # SIFRE SIFIRLA
    if request.method == 'POST' and 'sifre_sifirla' in request.form:
        cursor.execute("UPDATE kullanicilar SET sifre=%s WHERE kullanici_id=%s",
                       (request.form['yeni_sifre'], request.form['kullanici_id']))
        db.commit()
        flash(f'Sifre sifirlandi: {request.form["yeni_sifre"]}', 'success')

    # ARAC SIL
    if request.method == 'POST' and 'arac_sil' in request.form:
        arac_id = request.form['arac_id']
        cursor.execute("DELETE FROM arac_alim_talebi WHERE arac_id=%s", (arac_id,))
        cursor.execute("DELETE FROM araclar WHERE arac_id=%s", (arac_id,))
        db.commit()
        flash('Arac silindi!', 'success')

    # VERILERI CEK
    cursor.execute("""SELECT b.*, COUNT(DISTINCT a.arac_id) as arac_sayisi
                     FROM bayiler b
                     LEFT JOIN araclar a ON b.bayi_id = a.bayi_id
                     GROUP BY b.bayi_id ORDER BY b.bayi_adi""")
    bayiler = cursor.fetchall()

    cursor.execute("""SELECT a.*, b.bayi_adi FROM araclar a
                     JOIN bayiler b ON a.bayi_id = b.bayi_id
                     ORDER BY a.ilan_tarihi DESC""")
    araclar = cursor.fetchall()

    cursor.execute("SELECT * FROM kullanicilar ORDER BY kayit_tarihi DESC")
    kullanicilar = cursor.fetchall()

    cursor.execute("""SELECT aat.*, a.marka, a.model, a.fiyat, b.bayi_adi,
                     k.ad, k.soyad FROM arac_alim_talebi aat
                     JOIN araclar a ON aat.arac_id = a.arac_id
                     JOIN bayiler b ON a.bayi_id = b.bayi_id
                     JOIN kullanicilar k ON aat.musteri_id = k.kullanici_id
                     ORDER BY aat.talep_tarihi DESC""")
    alim_talepleri = cursor.fetchall()

    cursor.execute("""SELECT ast.*, b.bayi_adi, k.ad, k.soyad
                     FROM arac_satim_talebi ast
                     JOIN bayiler b ON ast.bayi_id = b.bayi_id
                     JOIN kullanicilar k ON ast.musteri_id = k.kullanici_id
                     ORDER BY ast.talep_tarihi DESC""")
    satim_talepleri = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('admin.html',
                           bayiler=bayiler, araclar=araclar,
                           kullanicilar=kullanicilar,
                           alim_talepleri=alim_talepleri,
                           satim_talepleri=satim_talepleri)


# ============================================
# BAYI PANEL
# ============================================
@app.route('/bayi', methods=['GET', 'POST'])
def bayi():
    if 'kullanici_id' not in session or session['yetki'] != 'personel':
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT bayi_id FROM personeller WHERE kullanici_id=%s", (session['kullanici_id'],))
    bayi_info = cursor.fetchone()
    if not bayi_info:
        cursor.close()
        db.close()
        return redirect(url_for('logout'))
    bayi_id = bayi_info['bayi_id']

    # ARAC EKLE
    if request.method == 'POST' and 'arac_ekle' in request.form:
        cursor.execute("""INSERT INTO araclar 
                        (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, 
                         fiyat, plaka, arac_durumu, aciklama, ilan_tarihi)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Satista', %s, NOW())""",
                       (bayi_id, request.form['marka'], request.form['model'],
                        request.form['yil'], request.form['kilometre'],
                        request.form['yakit'], request.form['vites'], request.form['renk'],
                        request.form['fiyat'], request.form['plaka'],
                        request.form.get('aciklama', '')))
        db.commit()
        flash('Arac eklendi!', 'success')

    # PERSONEL EKLE
    if request.method == 'POST' and 'personel_ekle' in request.form:
        try:
            cursor.execute("""INSERT INTO kullanicilar 
                            (ad, soyad, email, telefon, sifre, yetki, kayit_tarihi)
                            VALUES (%s, %s, %s, %s, %s, 'personel', NOW())""",
                           (request.form['ad'], request.form['soyad'],
                            request.form['email'], request.form['telefon'],
                            request.form['sifre']))
            db.commit()
            yeni_kullanici_id = cursor.lastrowid

            cursor.execute("""INSERT INTO personeller (kullanici_id, bayi_id, gorev, ise_giris_tarihi)
                            VALUES (%s, %s, %s, CURDATE())""",
                           (yeni_kullanici_id, bayi_id, request.form['gorev']))
            db.commit()
            flash('Personel eklendi!', 'success')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')

    # ARAC SIL
    if request.method == 'POST' and 'arac_sil' in request.form:
        arac_id = request.form['arac_id']
        cursor.execute("DELETE FROM arac_alim_talebi WHERE arac_id=%s", (arac_id,))
        cursor.execute("DELETE FROM araclar WHERE arac_id=%s AND bayi_id=%s", (arac_id, bayi_id))
        db.commit()
        flash('Arac silindi!', 'success')

    # ALIM TALEBI ONAY/RED
    if request.method == 'POST' and 'alim_durum' in request.form:
        durum = request.form['durum']
        alim_talep_id = request.form['alim_talep_id']
        arac_id = request.form['arac_id']
        cursor.execute("UPDATE arac_alim_talebi SET durum=%s WHERE alim_talep_id=%s",
                       (durum, alim_talep_id))
        if durum == 'Onaylandi':
            cursor.execute("UPDATE araclar SET arac_durumu='Satildi' WHERE arac_id=%s", (arac_id,))
        db.commit()
        flash(f'Talep guncellendi: {durum}', 'success')

    # SATIM TALEBI ONAY/RED
    if request.method == 'POST' and 'satim_durum' in request.form:
        durum = request.form['durum']
        satim_talep_id = request.form['satim_talep_id']
        cursor.execute("UPDATE arac_satim_talebi SET durum=%s WHERE satim_talep_id=%s",
                       (durum, satim_talep_id))
        if durum == 'Satin Alindi':
            cursor.execute("SELECT * FROM arac_satim_talebi WHERE satim_talep_id=%s", (satim_talep_id,))
            talep = cursor.fetchone()
            cursor.execute("""INSERT INTO araclar 
                            (bayi_id, marka, model, yil, kilometre, yakit, vites, renk,
                             fiyat, plaka, arac_durumu, aciklama, ilan_tarihi)
                            VALUES (%s, %s, %s, %s, %s, 'Benzin', 'Manuel', '-',
                                    %s, '-', 'Satista', 'Musteriden alindi', NOW())""",
                           (bayi_id, talep['marka'], talep['model'], talep['yil'],
                            talep['kilometre'], talep['fiyat_beklentisi']))
        db.commit()
        flash(f'Talep guncellendi: {durum}', 'success')

    cursor.execute("SELECT * FROM bayiler WHERE bayi_id=%s", (bayi_id,))
    bayi = cursor.fetchone()

    cursor.execute("SELECT * FROM araclar WHERE bayi_id=%s ORDER BY ilan_tarihi DESC", (bayi_id,))
    araclar = cursor.fetchall()

    cursor.execute("""SELECT k.*, p.personel_id, p.gorev FROM personeller p
                     JOIN kullanicilar k ON p.kullanici_id = k.kullanici_id
                     WHERE p.bayi_id=%s ORDER BY k.ad""", (bayi_id,))
    personeller = cursor.fetchall()

    cursor.execute("""SELECT aat.*, a.marka, a.model, a.fiyat,
                     k.ad, k.soyad, k.email, k.telefon
                     FROM arac_alim_talebi aat
                     JOIN araclar a ON aat.arac_id = a.arac_id
                     JOIN kullanicilar k ON aat.musteri_id = k.kullanici_id
                     WHERE a.bayi_id=%s ORDER BY aat.talep_tarihi DESC""", (bayi_id,))
    alim_talepleri = cursor.fetchall()

    cursor.execute("""SELECT ast.*, k.ad, k.soyad, k.email, k.telefon
                     FROM arac_satim_talebi ast
                     JOIN kullanicilar k ON ast.musteri_id = k.kullanici_id
                     WHERE ast.bayi_id=%s ORDER BY ast.talep_tarihi DESC""", (bayi_id,))
    satim_talepleri = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('bayi.html',
                           bayi=bayi, araclar=araclar,
                           personeller=personeller,
                           alim_talepleri=alim_talepleri,
                           satim_talepleri=satim_talepleri)


# ============================================
# MUSTERI PANEL
# ============================================
@app.route('/musteri', methods=['GET', 'POST'])
def musteri():
    if 'kullanici_id' not in session or session['yetki'] != 'musteri':
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST' and 'alim_talep' in request.form:
        cursor.execute("""INSERT INTO arac_alim_talebi 
                        (musteri_id, arac_id, odeme_tipi, durum, notlar, talep_tarihi)
                        VALUES (%s, %s, %s, 'Beklemede', %s, NOW())""",
                       (session['kullanici_id'], request.form['arac_id'],
                        request.form['odeme_tipi'], request.form.get('notlar', '')))
        db.commit()
        flash('Alim talebi gonderildi!', 'success')

    if request.method == 'POST' and 'satim_talep' in request.form:
        cursor.execute("""INSERT INTO arac_satim_talebi 
                        (musteri_id, bayi_id, marka, model, yil, kilometre, 
                         fiyat_beklentisi, ekspertiz, durum, talep_tarihi)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Beklemede', NOW())""",
                       (session['kullanici_id'], request.form['bayi_id'],
                        request.form['marka'], request.form['model'], request.form['yil'],
                        request.form['kilometre'], request.form['fiyat_beklentisi'],
                        request.form['ekspertiz']))
        db.commit()
        flash('Satim talebi gonderildi!', 'success')

    cursor.execute("""SELECT a.*, b.bayi_adi, b.sehir FROM araclar a
                     JOIN bayiler b ON a.bayi_id = b.bayi_id
                     WHERE a.arac_durumu='Satista'
                     ORDER BY a.ilan_tarihi DESC""")
    araclar = cursor.fetchall()

    cursor.execute("SELECT * FROM bayiler ORDER BY bayi_adi")
    bayiler = cursor.fetchall()

    cursor.execute("""SELECT aat.*, a.marka, a.model, a.fiyat, b.bayi_adi
                     FROM arac_alim_talebi aat
                     JOIN araclar a ON aat.arac_id = a.arac_id
                     JOIN bayiler b ON a.bayi_id = b.bayi_id
                     WHERE aat.musteri_id=%s
                     ORDER BY aat.talep_tarihi DESC""", (session['kullanici_id'],))
    alim_talepleri = cursor.fetchall()

    cursor.execute("""SELECT ast.*, b.bayi_adi FROM arac_satim_talebi ast
                     JOIN bayiler b ON ast.bayi_id = b.bayi_id
                     WHERE ast.musteri_id=%s
                     ORDER BY ast.talep_tarihi DESC""", (session['kullanici_id'],))
    satim_talepleri = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('musteri.html',
                           araclar=araclar, bayiler=bayiler,
                           alim_talepleri=alim_talepleri,
                           satim_talepleri=satim_talepleri)


if __name__ == '__main__':
    app.run(debug=True, port=5000)