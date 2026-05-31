from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Uygulamayı başlat
uygulama = Flask(__name__)
uygulama.secret_key = 'gizli123'

# Fotoğraf yükleme ayarları
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
# Dekont/fatura için PDF de kabul edilir
BELGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
uygulama.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def izin_verilen(dosya_adi):
    return '.' in dosya_adi and dosya_adi.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def belge_izin_verilen(dosya_adi):
    return '.' in dosya_adi and dosya_adi.rsplit('.', 1)[1].lower() in BELGE_EXTENSIONS

# Veritabanına bağlan
def baglan():
    try:
        baglanti = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='oto_galeri',
            autocommit=False
        )
        return baglanti
    except mysql.connector.Error as err:
        print(f"Veritabanı bağlantı hatası: {err}")
        return None


# Ana sayfa - kullanıcıya göre yönlendir
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


# GİRİŞ
@uygulama.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        email = request.form.get('email', '')
        sifre = request.form.get('sifre', '')

        db = baglan()
        if not db:
            flash('Veritabanı bağlantısı başarısız!', 'error')
            return render_template('giris.html')

        im = db.cursor(dictionary=True)
        try:
            im.execute("SELECT * FROM kullanicilar WHERE email=%s AND sifre=%s", (email, sifre))
            kul = im.fetchone()
            
            if kul:
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
        except Exception as e:
            flash(f'Hata: {str(e)}', 'error')
        finally:
            im.close()
            db.close()

    return render_template('giris.html')


# ÇIKIŞ
@uygulama.route('/cikis')
def cikis():
    session.clear()
    return redirect(url_for('giris'))


# KAYIT (sadece müşteri)
@uygulama.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        ad_soyad = request.form.get('ad_soyad', '')[:50]
        email    = request.form.get('email', '')[:100]
        telefon  = request.form.get('telefon', '')[:11]
        sifre    = request.form.get('sifre', '')[:20]

        db = baglan()
        if not db:
            flash('Veritabanı bağlantısı başarısız!', 'error')
            return render_template('kayit.html')

        im = db.cursor()
        try:
            im.execute("""INSERT INTO kullanicilar (ad_soyad, email, telefon, sifre, yetki)
                          VALUES (%s, %s, %s, %s, 'musteri')""",
                       (ad_soyad, email, telefon, sifre))
            db.commit()
            flash('Kayit basarili! Giris yapabilirsiniz.', 'success')
            return redirect(url_for('giris'))
        except Exception as e:
            db.rollback()
            flash('Bu email zaten kullaniliyor!', 'error')
        finally:
            im.close()
            db.close()

    return render_template('kayit.html')


# PROFİL GÜNCELLE (tüm kullanıcılar - popup'tan POST alır)
@uygulama.route('/profil', methods=['POST'])
def profil():
    if 'id' not in session:
        return redirect(url_for('giris'))

    redirect_url = request.form.get('popup_redirect', url_for('anasayfa'))

    db = baglan()
    if not db:
        flash('Veritabanı bağlantısı başarısız!', 'error')
        return redirect(redirect_url)

    im = db.cursor(dictionary=True)

    try:
        yeni_ad      = request.form.get('ad_soyad', '').strip()[:50]
        yeni_telefon = request.form.get('telefon', '').strip()[:11]
        yeni_email   = request.form.get('email', '').strip()[:100]
        yeni_sifre   = request.form.get('sifre', '').strip()[:20]
        mevcut_sifre = request.form.get('mevcut_sifre', '').strip()

        im.execute("SELECT sifre FROM kullanicilar WHERE kullanici_id=%s", (session['id'],))
        kul = im.fetchone()

        if not kul or kul['sifre'] != mevcut_sifre:
            flash('Mevcut sifre yanlis!', 'error')
            session['profil_popup_ac'] = True
        else:
            if yeni_sifre:
                im.execute("""UPDATE kullanicilar SET ad_soyad=%s, telefon=%s, email=%s, sifre=%s
                              WHERE kullanici_id=%s""",
                           (yeni_ad, yeni_telefon, yeni_email, yeni_sifre, session['id']))
            else:
                im.execute("""UPDATE kullanicilar SET ad_soyad=%s, telefon=%s, email=%s
                              WHERE kullanici_id=%s""",
                           (yeni_ad, yeni_telefon, yeni_email, session['id']))
            db.commit()
            session['ad_soyad'] = yeni_ad
            session['email']    = yeni_email
            session['telefon']  = yeni_telefon
            session.pop('profil_popup_ac', None)
            flash('Profil guncellendi!', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Hata: {str(e)}', 'error')
        session['profil_popup_ac'] = True
    finally:
        im.close()
        db.close()

    return redirect(redirect_url)


# ============================================================================
# PAKET C: FAVORİ YÖNETIMI (YENİ ROUTE'LAR)
# ============================================================================

# Favoriye ekle / çıkar (AJAX)
@uygulama.route('/api/favori-toggle', methods=['POST'])
def favori_toggle():
    if 'id' not in session:
        return jsonify({'success': False, 'message': 'Giriş gerekli'}), 401

    data = request.get_json()
    arac_id = data.get('arac_id')
    
    if not arac_id:
        return jsonify({'success': False, 'message': 'Araç ID gerekli'}), 400

    db = baglan()
    if not db:
        return jsonify({'success': False, 'message': 'DB hatası'}), 500

    im = db.cursor(dictionary=True)
    
    try:
        # Kontrol: Bu araç favoride mi?
        im.execute("SELECT favori_id FROM favoriler WHERE musteri_id=%s AND arac_id=%s", 
                   (session['id'], arac_id))
        var_mi = im.fetchone()

        if var_mi:
            # Favoriden çıkar
            im.execute("DELETE FROM favoriler WHERE musteri_id=%s AND arac_id=%s", 
                       (session['id'], arac_id))
            db.commit()
            return jsonify({'success': True, 'action': 'removed'})
        else:
            # Favoriye ekle
            im.execute("""INSERT INTO favoriler (musteri_id, arac_id) 
                          VALUES (%s, %s)""", (session['id'], arac_id))
            db.commit()
            return jsonify({'success': True, 'action': 'added'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        im.close()
        db.close()


# Müşterinin favori listesini getir
@uygulama.route('/api/favorilerim')
def favorilerim_api():
    if 'id' not in session:
        return jsonify({'success': False}), 401

    db = baglan()
    if not db:
        return jsonify({'success': False}), 500

    im = db.cursor(dictionary=True)

    try:
        im.execute("""SELECT arac_id FROM favoriler WHERE musteri_id=%s""", (session['id'],))
        favoriler = im.fetchall()
        favori_ids = [f['arac_id'] for f in favoriler]
        return jsonify({'success': True, 'favoriler': favori_ids})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        im.close()
        db.close()


# Favoriler popup için araç detaylarıyla birlikte getir
@uygulama.route('/api/favorilerim-detay')
def favorilerim_detay():
    if 'id' not in session:
        return jsonify({'success': False}), 401

    db = baglan()
    if not db:
        return jsonify({'success': False}), 500

    im = db.cursor(dictionary=True)

    try:
        im.execute("""SELECT a.arac_id, a.marka, a.model, a.yil, a.kilometre, 
                             a.yakit, a.fiyat, a.foto_url, b.bayi_adi, b.sehir
                      FROM favoriler f
                      JOIN araclar a ON f.arac_id = a.arac_id
                      JOIN bayiler b ON a.bayi_id = b.bayi_id
                      WHERE f.musteri_id = %s
                      ORDER BY f.eklenme_tarihi DESC""", (session['id'],))
        araclar = im.fetchall()
        return jsonify({'success': True, 'araclar': araclar})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        im.close()
        db.close()


# ============================================================================
# BELGE YÖNETIMI - Dekont (müşteri) & Fatura (bayi)
# ============================================================================

# Belge yükle (dekont veya fatura)
@uygulama.route('/belge-yukle', methods=['POST'])
def belge_yukle():
    if 'id' not in session:
        return redirect(url_for('giris'))

    talep_tipi = request.form.get('talep_tipi')   # 'alim' / 'satim'
    talep_id   = request.form.get('talep_id')
    belge_tipi = request.form.get('belge_tipi')    # 'dekont' / 'fatura'
    redirect_url = request.form.get('redirect_url', url_for('anasayfa'))

    db = baglan()
    if not db:
        flash('Veritabanı bağlantısı başarısız!', 'error')
        return redirect(redirect_url)

    im = db.cursor(dictionary=True)

    try:
        if 'belge' not in request.files:
            flash('Dosya seçilmedi!', 'error')
            return redirect(redirect_url)

        belge = request.files['belge']
        if not belge or not belge.filename:
            flash('Dosya seçilmedi!', 'error')
            return redirect(redirect_url)

        if not belge_izin_verilen(belge.filename):
            flash('Sadece PDF, JPG, PNG yükleyebilirsiniz!', 'error')
            return redirect(redirect_url)

        # Benzersiz dosya adı (talep tipi + id + tip + orijinal ad)
        guvenli_ad = secure_filename(belge.filename)
        yeni_ad = f"{belge_tipi}_{talep_tipi}_{talep_id}_{guvenli_ad}"
        belge.save(os.path.join(uygulama.config['UPLOAD_FOLDER'], yeni_ad))

        # Aynı talep+tip için eski belge varsa sil (yeni yüklenenle değiştir)
        im.execute("""DELETE FROM belgeler 
                      WHERE talep_tipi=%s AND talep_id=%s AND belge_tipi=%s""",
                   (talep_tipi, talep_id, belge_tipi))

        im.execute("""INSERT INTO belgeler 
                      (talep_tipi, talep_id, belge_tipi, dosya_adi, yukleyen_id)
                      VALUES (%s, %s, %s, %s, %s)""",
                   (talep_tipi, talep_id, belge_tipi, yeni_ad, session['id']))
        db.commit()
        
        belge_adi = 'Dekont' if belge_tipi == 'dekont' else 'Fatura'
        flash(f'{belge_adi} basariyla yuklendi!', 'success')
    except Exception as e:
        db.rollback()
        flash('Hata: ' + str(e), 'error')
    finally:
        im.close()
        db.close()

    return redirect(redirect_url)


# Belgeleri getir (bir talep için) - JSON
@uygulama.route('/api/belgeler/<talep_tipi>/<int:talep_id>')
def belgeler_getir(talep_tipi, talep_id):
    if 'id' not in session:
        return jsonify({'success': False}), 401

    db = baglan()
    if not db:
        return jsonify({'success': False}), 500

    im = db.cursor(dictionary=True)

    try:
        im.execute("""SELECT belge_id, belge_tipi, dosya_adi, yukleme_tarihi
                      FROM belgeler
                      WHERE talep_tipi=%s AND talep_id=%s
                      ORDER BY yukleme_tarihi DESC""",
                   (talep_tipi, talep_id))
        belgeler = im.fetchall()
        # tarihi string'e çevir
        for b in belgeler:
            if b['yukleme_tarihi']:
                b['yukleme_tarihi'] = b['yukleme_tarihi'].strftime('%d.%m.%Y %H:%M')
        return jsonify({'success': True, 'belgeler': belgeler})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        im.close()
        db.close()


# ADMİN PANELİ
@uygulama.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'id' not in session or session['yetki'] != 'admin':
        return redirect(url_for('giris'))

    db = baglan()
    if not db:
        flash('Veritabanı bağlantısı başarısız!', 'error')
        return render_template('admin.html')

    im = db.cursor(dictionary=True)

    try:
        # Yeni bayi ekle
        if request.method == 'POST' and 'bayi_ekle' in request.form:
            try:
                im.execute("""INSERT INTO bayiler (bayi_adi, sehir, adres, telefon, email)
                              VALUES (%s, %s, %s, %s, %s)""",
                           (request.form['bayi_adi'][:50], request.form['sehir'][:30],
                            request.form['adres'][:100],   request.form['b_telefon'][:11],
                            request.form['b_email'][:100]))
                yeni_bayi_id = im.lastrowid

                im.execute("""INSERT INTO kullanicilar (ad_soyad, email, telefon, sifre, yetki)
                              VALUES (%s, %s, %s, %s, 'personel')""",
                           (request.form['ad_soyad'][:50],  request.form['k_email'][:100],
                            request.form['k_telefon'][:11], request.form['k_sifre'][:20]))
                yeni_kul_id = im.lastrowid

                im.execute("""INSERT INTO personeller (kullanici_id, bayi_id, gorev)
                              VALUES (%s, %s, 'Yetkili')""", (yeni_kul_id, yeni_bayi_id))
                db.commit()
                flash('Bayi eklendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Bayi güncelle
        if request.method == 'POST' and 'bayi_guncelle' in request.form:
            try:
                im.execute("""UPDATE bayiler SET bayi_adi=%s, sehir=%s, adres=%s, telefon=%s, email=%s
                              WHERE bayi_id=%s""",
                           (request.form['bayi_adi'][:50], request.form['sehir'][:30],
                            request.form['adres'][:100],   request.form['b_telefon'][:11],
                            request.form['b_email'][:100], request.form['bayi_id']))
                db.commit()
                flash('Bayi guncellendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Bayi sil
        if request.method == 'POST' and 'bayi_sil' in request.form:
            try:
                bid = request.form['bayi_id']
                im.execute("DELETE FROM arac_alim_talebi WHERE arac_id IN (SELECT arac_id FROM araclar WHERE bayi_id=%s)", (bid,))
                im.execute("DELETE FROM arac_satim_talebi WHERE bayi_id=%s", (bid,))
                im.execute("DELETE FROM araclar WHERE bayi_id=%s", (bid,))
                im.execute("SELECT kullanici_id FROM personeller WHERE bayi_id=%s", (bid,))
                personeller_list = im.fetchall()
                im.execute("DELETE FROM personeller WHERE bayi_id=%s", (bid,))
                for p in personeller_list:
                    im.execute("DELETE FROM kullanicilar WHERE kullanici_id=%s", (p['kullanici_id'],))
                im.execute("DELETE FROM bayiler WHERE bayi_id=%s", (bid,))
                db.commit()
                flash('Bayi silindi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Kullanıcı güncelle
        if request.method == 'POST' and 'kullanici_guncelle' in request.form:
            try:
                kid = request.form['kullanici_id']
                yeni_ad      = request.form.get('ad_soyad', '')[:50]
                yeni_email   = request.form.get('email', '')[:100]
                yeni_telefon = request.form.get('telefon', '')[:11]
                yeni_yetki   = request.form.get('yetki', 'musteri')
                yeni_sifre   = request.form.get('yeni_sifre', '').strip()[:20]
                
                if yeni_sifre:
                    im.execute("""UPDATE kullanicilar SET ad_soyad=%s, email=%s, telefon=%s, yetki=%s, sifre=%s
                                  WHERE kullanici_id=%s""",
                               (yeni_ad, yeni_email, yeni_telefon, yeni_yetki, yeni_sifre, kid))
                else:
                    im.execute("""UPDATE kullanicilar SET ad_soyad=%s, email=%s, telefon=%s, yetki=%s
                                  WHERE kullanici_id=%s""",
                               (yeni_ad, yeni_email, yeni_telefon, yeni_yetki, kid))
                db.commit()
                flash('Kullanici guncellendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Kullanıcı sil
        if request.method == 'POST' and 'kullanici_sil' in request.form:
            try:
                kid = request.form['kullanici_id']
                im.execute("DELETE FROM arac_alim_talebi WHERE musteri_id=%s", (kid,))
                im.execute("DELETE FROM arac_satim_talebi WHERE musteri_id=%s", (kid,))
                im.execute("DELETE FROM personeller WHERE kullanici_id=%s", (kid,))
                im.execute("DELETE FROM kullanicilar WHERE kullanici_id=%s", (kid,))
                db.commit()
                flash('Kullanici silindi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Araç sil (admin)
        if request.method == 'POST' and 'arac_sil' in request.form:
            try:
                aid = request.form['arac_id']
                im.execute("DELETE FROM arac_alim_talebi WHERE arac_id=%s", (aid,))
                im.execute("DELETE FROM favoriler WHERE arac_id=%s", (aid,))
                im.execute("DELETE FROM araclar WHERE arac_id=%s", (aid,))
                db.commit()
                flash('Arac silindi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Araç güncelle (admin)
        if request.method == 'POST' and 'arac_guncelle' in request.form:
            try:
                aid = request.form['arac_id']
                im.execute("""UPDATE araclar SET marka=%s, model=%s, yil=%s, kilometre=%s,
                              yakit=%s, vites=%s, renk=%s, fiyat=%s, plaka=%s, arac_durumu=%s,
                              aciklama=%s, hasar_durumu=%s
                              WHERE arac_id=%s""",
                           (request.form['marka'][:30], request.form['model'][:30],
                            request.form['yil'],         request.form['kilometre'],
                            request.form['yakit'],       request.form['vites'],
                            request.form['renk'][:15],   request.form['fiyat'],
                            request.form['plaka'][:10],  request.form['arac_durumu'],
                            request.form.get('aciklama', '')[:500],
                            request.form.get('hasar_durumu', 'Belirtilmemis'), aid))
                db.commit()
                flash('Arac guncellendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Personel ekle (admin)
        if request.method == 'POST' and 'personel_ekle' in request.form:
            try:
                im.execute("""INSERT INTO kullanicilar (ad_soyad, email, telefon, sifre, yetki)
                              VALUES (%s, %s, %s, %s, 'personel')""",
                           (request.form['p_ad_soyad'][:50], request.form['p_email'][:100],
                            request.form['p_telefon'][:11],  request.form['p_sifre'][:20]))
                db.commit()
                yeni_id = im.lastrowid
                im.execute("INSERT INTO personeller (kullanici_id, bayi_id, gorev) VALUES (%s, %s, %s)",
                           (yeni_id, request.form['p_bayi_id'], request.form['p_gorev'][:30]))
                db.commit()
                flash('Personel eklendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Personel güncelle (admin)
        if request.method == 'POST' and 'personel_guncelle' in request.form:
            try:
                im.execute("""UPDATE kullanicilar SET ad_soyad=%s, email=%s, telefon=%s
                              WHERE kullanici_id=%s""",
                           (request.form['ad_soyad'][:50], request.form['email'][:100],
                            request.form['telefon'][:11],  request.form['kullanici_id']))
                im.execute("""UPDATE personeller SET gorev=%s, bayi_id=%s WHERE personel_id=%s""",
                           (request.form['gorev'][:30], request.form['bayi_id'], request.form['personel_id']))
                db.commit()
                flash('Personel guncellendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Personel sil (admin)
        if request.method == 'POST' and 'personel_sil' in request.form:
            try:
                pid = request.form['personel_id']
                kid = request.form['kullanici_id']
                im.execute("DELETE FROM personeller WHERE personel_id=%s", (pid,))
                im.execute("DELETE FROM kullanicilar WHERE kullanici_id=%s", (kid,))
                db.commit()
                flash('Personel silindi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Verileri çek
        im.execute("SELECT b.*, COUNT(a.arac_id) as arac_sayisi FROM bayiler b LEFT JOIN araclar a ON b.bayi_id=a.bayi_id GROUP BY b.bayi_id")
        bayiler = im.fetchall()

        im.execute("SELECT a.*, b.bayi_adi FROM araclar a JOIN bayiler b ON a.bayi_id=b.bayi_id")
        araclar = im.fetchall()

        im.execute("SELECT * FROM kullanicilar")
        kullanicilar = im.fetchall()

        im.execute("""SELECT p.personel_id, p.kullanici_id, p.gorev, p.bayi_id,
                             k.ad_soyad, k.email, k.telefon, b.bayi_adi
                      FROM personeller p
                      JOIN kullanicilar k ON p.kullanici_id=k.kullanici_id
                      JOIN bayiler b ON p.bayi_id=b.bayi_id""")
        personeller = im.fetchall()

        im.execute("""SELECT t.*, a.marka, a.model, a.fiyat, a.foto_url, b.bayi_adi, k.ad_soyad
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

    finally:
        im.close()
        db.close()

    return render_template('admin.html',
                           bayiler=bayiler, araclar=araclar,
                           kullanicilar=kullanicilar,
                           personeller=personeller,
                           alim_talepleri=alim_talepleri,
                           satim_talepleri=satim_talepleri)


# BAYİ PANELİ
@uygulama.route('/bayi', methods=['GET', 'POST'])
def bayi_panel():
    if 'id' not in session or session['yetki'] != 'personel':
        return redirect(url_for('giris'))

    aktif_sekme = 'araclar'

    db = baglan()
    if not db:
        flash('Veritabanı bağlantısı başarısız!', 'error')
        return render_template('bayi.html')

    im = db.cursor(dictionary=True)

    try:
        # Bu kullanıcının bayisini bul
        im.execute("SELECT bayi_id FROM personeller WHERE kullanici_id=%s", (session['id'],))
        sonuc = im.fetchone()
        if not sonuc:
            return redirect(url_for('cikis'))
        bayi_id = sonuc['bayi_id']

        # Araç ekle (fotoğraf destekli) - PAKET A güncelleme
        if request.method == 'POST' and 'arac_ekle' in request.form:
            aktif_sekme = 'araclar'
            try:
                foto_adi = 'default-car.jpg'
                if 'foto' in request.files:
                    foto = request.files['foto']
                    if foto and foto.filename and izin_verilen(foto.filename):
                        guvenli_ad = secure_filename(foto.filename)
                        foto.save(os.path.join(uygulama.config['UPLOAD_FOLDER'], guvenli_ad))
                        foto_adi = guvenli_ad

                im.execute("""INSERT INTO araclar 
                              (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, fiyat, 
                               plaka, arac_durumu, foto_url, aciklama, hasar_durumu)
                              VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Satista',%s,%s,%s)""",
                           (bayi_id,
                            request.form['marka'][:30],    request.form['model'][:30],
                            request.form['yil'],            request.form['kilometre'],
                            request.form['yakit'],          request.form['vites'],
                            request.form['renk'][:15],      request.form['fiyat'],
                            request.form['plaka'][:10],     foto_adi,
                            request.form.get('aciklama', '')[:500],
                            request.form.get('hasar_durumu', 'Belirtilmemis')))
                db.commit()
                flash('Arac basariyla eklendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')
            return redirect(url_for('bayi_panel') + '?sekme=araclar')

        # Araç sil
        if request.method == 'POST' and 'arac_sil' in request.form:
            aktif_sekme = 'araclar'
            try:
                aid = request.form['arac_id']
                im.execute("DELETE FROM arac_alim_talebi WHERE arac_id=%s", (aid,))
                im.execute("DELETE FROM favoriler WHERE arac_id=%s", (aid,))
                im.execute("DELETE FROM araclar WHERE arac_id=%s AND bayi_id=%s", (aid, bayi_id))
                db.commit()
                flash('Arac silindi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')
            return redirect(url_for('bayi_panel') + '?sekme=araclar')

        # Araç güncelle (bayi) - PAKET A güncelleme
        if request.method == 'POST' and 'arac_guncelle' in request.form:
            aktif_sekme = 'araclar'
            try:
                aid = request.form['arac_id']
                im.execute("SELECT foto_url FROM araclar WHERE arac_id=%s", (aid,))
                mevcut = im.fetchone()
                foto_adi = mevcut['foto_url'] if mevcut and mevcut['foto_url'] else 'default-car.jpg'

                if 'foto' in request.files:
                    foto = request.files['foto']
                    if foto and foto.filename and izin_verilen(foto.filename):
                        guvenli_ad = secure_filename(foto.filename)
                        foto.save(os.path.join(uygulama.config['UPLOAD_FOLDER'], guvenli_ad))
                        foto_adi = guvenli_ad

                im.execute("""UPDATE araclar SET marka=%s, model=%s, yil=%s, kilometre=%s,
                              yakit=%s, vites=%s, renk=%s, fiyat=%s, plaka=%s, arac_durumu=%s, 
                              foto_url=%s, aciklama=%s, hasar_durumu=%s
                              WHERE arac_id=%s AND bayi_id=%s""",
                           (request.form['marka'][:30], request.form['model'][:30],
                            request.form['yil'],         request.form['kilometre'],
                            request.form['yakit'],       request.form['vites'],
                            request.form['renk'][:15],   request.form['fiyat'],
                            request.form['plaka'][:10],  request.form['arac_durumu'],
                            foto_adi, 
                            request.form.get('aciklama', '')[:500],
                            request.form.get('hasar_durumu', 'Belirtilmemis'),
                            aid, bayi_id))
                db.commit()
                flash('Arac guncellendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')
            return redirect(url_for('bayi_panel') + '?sekme=araclar')

        # Alım talebi durumunu güncelle
        if request.method == 'POST' and 'alim_guncelle' in request.form:
            try:
                yeni_durum = request.form['durum']
                alim_id    = request.form['alim_id']
                arac_id    = request.form['arac_id']
                im.execute("UPDATE arac_alim_talebi SET durum=%s WHERE alim_id=%s", (yeni_durum, alim_id))
                if yeni_durum == 'Onaylandi':
                    im.execute("UPDATE araclar SET arac_durumu='Satildi' WHERE arac_id=%s", (arac_id,))
                db.commit()
                flash('Talep guncellendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')
            return redirect(url_for('bayi_panel') + '?sekme=alim')

        # Satım talebi durumunu güncelle
        if request.method == 'POST' and 'satim_guncelle' in request.form:
            try:
                yeni_durum = request.form['durum']
                satim_id   = request.form['satim_id']
                im.execute("UPDATE arac_satim_talebi SET durum=%s WHERE satim_id=%s", (yeni_durum, satim_id))
                if yeni_durum == 'Satin Alindi':
                    im.execute("SELECT * FROM arac_satim_talebi WHERE satim_id=%s", (satim_id,))
                    talep = im.fetchone()
                    # Fotoğrafı, plakayı ve tüm bilgileri talepten al
                    foto  = talep.get('foto_url') or 'default-car.jpg'
                    plaka = talep.get('plaka') or '-'
                    yakit = talep.get('yakit') or 'Belirtilmemis'
                    vites = talep.get('vites') or 'Belirtilmemis'
                    renk  = talep.get('renk') or '-'
                    im.execute("""INSERT INTO araclar
                                  (bayi_id, marka, model, yil, kilometre, yakit, vites, renk,
                                   fiyat, plaka, arac_durumu, foto_url)
                                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Satista', %s)""",
                               (bayi_id, talep['marka'], talep['model'], talep['yil'],
                                talep['kilometre'], yakit, vites, renk,
                                talep['fiyat_beklentisi'], plaka, foto))
                db.commit()
                flash('Talep guncellendi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')
            return redirect(url_for('bayi_panel') + '?sekme=satim')

        # URL parametresinden aktif sekmeyi al (GET isteği)
        aktif_sekme = request.args.get('sekme', 'araclar')

        # Verileri çek
        im.execute("SELECT * FROM bayiler WHERE bayi_id=%s", (bayi_id,))
        bayi = im.fetchone()

        im.execute("SELECT * FROM araclar WHERE bayi_id=%s", (bayi_id,))
        araclar = im.fetchall()

        im.execute("""SELECT k.kullanici_id, k.ad_soyad, k.email, k.telefon, p.gorev, p.personel_id
                      FROM personeller p
                      JOIN kullanicilar k ON p.kullanici_id=k.kullanici_id
                      WHERE p.bayi_id=%s""", (bayi_id,))
        personeller = im.fetchall()

        im.execute("""SELECT t.*, a.marka, a.model, a.fiyat, a.foto_url, k.ad_soyad, k.telefon
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

        # Her talebe belge bilgisi ekle (dekont / fatura)
        def belge_ekle_bayi(talepler, tip):
            for t in talepler:
                tid = t['alim_id'] if tip == 'alim' else t['satim_id']
                im.execute("""SELECT belge_tipi, dosya_adi FROM belgeler
                              WHERE talep_tipi=%s AND talep_id=%s""", (tip, tid))
                belgeler = im.fetchall()
                t['dekont'] = None
                t['fatura'] = None
                for b in belgeler:
                    if b['belge_tipi'] == 'dekont':
                        t['dekont'] = b['dosya_adi']
                    elif b['belge_tipi'] == 'fatura':
                        t['fatura'] = b['dosya_adi']
        belge_ekle_bayi(alim_talepleri, 'alim')
        belge_ekle_bayi(satim_talepleri, 'satim')

    finally:
        im.close()
        db.close()

    return render_template('bayi.html',
                           bayi=bayi, araclar=araclar,
                           personeller=personeller,
                           alim_talepleri=alim_talepleri,
                           satim_talepleri=satim_talepleri,
                           aktif_sekme=aktif_sekme)


# MÜŞTERİ PANELİ - PAKET A + D (Filtreleme)
@uygulama.route('/musteri', methods=['GET', 'POST'])
def musteri_panel():
    if 'id' not in session or session['yetki'] != 'musteri':
        return redirect(url_for('giris'))

    db = baglan()
    if not db:
        flash('Veritabanı bağlantısı başarısız!', 'error')
        return render_template('musteri.html')

    im = db.cursor(dictionary=True)

    try:
        # Alım talebi gönder
        if request.method == 'POST' and 'alim_talep' in request.form:
            try:
                im.execute("""INSERT INTO arac_alim_talebi (musteri_id, arac_id, odeme_tipi, pazarlık_tutari, durum, talep_tarihi)
                              VALUES (%s, %s, %s, %s, 'Beklemede', NOW())""",
                           (session['id'], request.form['arac_id'], request.form['odeme_tipi'],
                            request.form.get('pazarlık_tutari', 0) or 0))
                db.commit()
                flash('Alim talebi gonderildi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # Satım talebi gönder (fotoğraf destekli)
        if request.method == 'POST' and 'satim_talep' in request.form:
            try:
                foto_adi = None
                if 'foto' in request.files:
                    foto = request.files['foto']
                    if foto and foto.filename and izin_verilen(foto.filename):
                        guvenli_ad = secure_filename(foto.filename)
                        foto.save(os.path.join(uygulama.config['UPLOAD_FOLDER'], guvenli_ad))
                        foto_adi = guvenli_ad
                im.execute("""INSERT INTO arac_satim_talebi
                              (musteri_id, bayi_id, marka, model, yil, kilometre,
                               fiyat_beklentisi, ekspertiz, plaka, yakit, vites, renk,
                               foto_url, durum, talep_tarihi)
                              VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Beklemede',NOW())""",
                           (session['id'],              request.form['bayi_id'],
                            request.form['marka'][:30], request.form['model'][:30],
                            request.form['yil'],         request.form['kilometre'],
                            request.form['fiyat'],       request.form['ekspertiz'],
                            request.form.get('plaka', ''),
                            request.form.get('yakit', 'Belirtilmemis'),
                            request.form.get('vites', 'Belirtilmemis'),
                            request.form.get('renk', ''), foto_adi))
                db.commit()
                flash('Satim talebi gonderildi!', 'success')
            except Exception as h:
                db.rollback()
                flash('Hata: ' + str(h), 'error')

        # ============================================================
        # PAKET D: FİLTRELEME VE SIRALAMA
        # ============================================================
        
        # Filtre parametrelerini al
        min_fiyat = request.args.get('min_fiyat', '', type=int) if request.args.get('min_fiyat', '').isdigit() else None
        max_fiyat = request.args.get('max_fiyat', '', type=int) if request.args.get('max_fiyat', '').isdigit() else None
        min_yil = request.args.get('min_yil', '', type=int) if request.args.get('min_yil', '').isdigit() else None
        max_yil = request.args.get('max_yil', '', type=int) if request.args.get('max_yil', '').isdigit() else None
        min_km = request.args.get('min_km', '', type=int) if request.args.get('min_km', '').isdigit() else None
        max_km = request.args.get('max_km', '', type=int) if request.args.get('max_km', '').isdigit() else None
        yakit = request.args.get('yakit', '')
        sira = request.args.get('sira', 'ilan_tarihi_desc')  # Varsayılan: en yeni
        arama = request.args.get('arama', '')

        # SQL sorgusunun temel kısmı
        sql_base = """SELECT a.*, b.bayi_adi, b.sehir FROM araclar a
                      JOIN bayiler b ON a.bayi_id=b.bayi_id
                      WHERE a.arac_durumu='Satista'"""
        
        params = []

        # Filtreleri ekle
        if min_fiyat is not None:
            sql_base += " AND a.fiyat >= %s"
            params.append(min_fiyat)
        if max_fiyat is not None:
            sql_base += " AND a.fiyat <= %s"
            params.append(max_fiyat)
        if min_yil is not None:
            sql_base += " AND a.yil >= %s"
            params.append(min_yil)
        if max_yil is not None:
            sql_base += " AND a.yil <= %s"
            params.append(max_yil)
        if min_km is not None:
            sql_base += " AND a.kilometre >= %s"
            params.append(min_km)
        if max_km is not None:
            sql_base += " AND a.kilometre <= %s"
            params.append(max_km)
        if yakit and yakit != '':
            sql_base += " AND a.yakit = %s"
            params.append(yakit)
        if arama and arama.strip():
            sql_base += " AND (a.marka LIKE %s OR a.model LIKE %s OR b.bayi_adi LIKE %s OR a.aciklama LIKE %s)"
            arama_param = f"%{arama}%"
            params.extend([arama_param, arama_param, arama_param, arama_param])

        # Sıralama ekle
        if sira == 'fiyat_asc':
            sql_base += " ORDER BY a.fiyat ASC"
        elif sira == 'fiyat_desc':
            sql_base += " ORDER BY a.fiyat DESC"
        elif sira == 'yil_asc':
            sql_base += " ORDER BY a.yil ASC"
        elif sira == 'yil_desc':
            sql_base += " ORDER BY a.yil DESC"
        elif sira == 'km_asc':
            sql_base += " ORDER BY a.kilometre ASC"
        elif sira == 'km_desc':
            sql_base += " ORDER BY a.kilometre DESC"
        else:  # ilan_tarihi_desc (varsayılan)
            sql_base += " ORDER BY a.ilan_tarihi DESC"

        im.execute(sql_base, params)
        araclar = im.fetchall()

        # Her araç görüntülenişini artır (PAKET A: goruntulenme)
        if araclar:
            for arac in araclar:
                im.execute("UPDATE araclar SET goruntulenme = goruntulenme + 1 WHERE arac_id=%s", 
                           (arac['arac_id'],))
            db.commit()

        # Tüm bayileri getir
        im.execute("SELECT * FROM bayiler")
        bayiler = im.fetchall()

        # Müşterinin alım taleplerini getir
        im.execute("""SELECT t.*, a.marka, a.model, a.fiyat, a.foto_url, b.bayi_adi
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

        # Her talebe belge bilgisi ekle (dekont / fatura)
        def belge_ekle(talepler, tip):
            for t in talepler:
                tid = t['alim_id'] if tip == 'alim' else t['satim_id']
                im.execute("""SELECT belge_tipi, dosya_adi FROM belgeler
                              WHERE talep_tipi=%s AND talep_id=%s""", (tip, tid))
                belgeler = im.fetchall()
                t['dekont'] = None
                t['fatura'] = None
                for b in belgeler:
                    if b['belge_tipi'] == 'dekont':
                        t['dekont'] = b['dosya_adi']
                    elif b['belge_tipi'] == 'fatura':
                        t['fatura'] = b['dosya_adi']
        belge_ekle(alim_taleplerim, 'alim')
        belge_ekle(satim_taleplerim, 'satim')

        # Müşterinin favorilerini getir (PAKET C)
        im.execute("SELECT arac_id FROM favoriler WHERE musteri_id=%s", (session['id'],))
        favoriler = im.fetchall()
        favori_ids = set([f['arac_id'] for f in favoriler])

    finally:
        im.close()
        db.close()

    return render_template('musteri.html',
                           araclar=araclar, bayiler=bayiler,
                           alim_talepleri=alim_taleplerim,
                           satim_talepleri=satim_taleplerim,
                           favori_ids=favori_ids,
                           # Filtre parametrelerini template'e gönder
                           min_fiyat=min_fiyat, max_fiyat=max_fiyat,
                           min_yil=min_yil, max_yil=max_yil,
                           min_km=min_km, max_km=max_km,
                           yakit=yakit, sira=sira, arama=arama)


if __name__ == '__main__':
    uygulama.run(debug=True, port=5000)