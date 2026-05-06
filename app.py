from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_12345'

# Veritabanı bağlantısı
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='oto_galeri'
    )

# ============================================
# ANA SAYFA VE LOGIN
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
            session['yetki'] = kullanici['yetki']
            flash('Giriş başarılı!', 'success')
            
            if kullanici['yetki'] == 'admin':
                return redirect(url_for('admin'))
            elif kullanici['yetki'] == 'personel':
                return redirect(url_for('bayi'))
            else:
                return redirect(url_for('musteri'))
        else:
            flash('Email veya şifre hatalı!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Çıkış yapıldı!', 'success')
    return redirect(url_for('login'))

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    """Yeni müşteri kaydı"""
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        email = request.form['email']
        telefon = request.form['telefon']
        sifre = request.form['sifre']
        
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                """INSERT INTO kullanicilar 
                (ad, soyad, email, telefon, sifre, yetki, kayit_tarihi)
                VALUES (%s, %s, %s, %s, %s, 'musteri', NOW())""",
                (ad, soyad, email, telefon, sifre)
            )
            db.commit()
            flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Bu email adresi zaten kullanılıyor!', 'error')
        finally:
            cursor.close()
            db.close()
    
    return render_template('kayit.html')

# ============================================
# ADMIN PANEL - TEK SAYFA
# ============================================

@app.route('/admin')
def admin():
    if 'kullanici_id' not in session or session['yetki'] != 'admin':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Bayiler
    cursor.execute("""
        SELECT b.*, 
               COUNT(DISTINCT a.arac_id) as arac_sayisi,
               COUNT(DISTINCT p.personel_id) as personel_sayisi
        FROM bayiler b
        LEFT JOIN araclar a ON b.bayi_id = a.bayi_id
        LEFT JOIN personeller p ON b.bayi_id = p.bayi_id
        GROUP BY b.bayi_id
    """)
    bayiler = cursor.fetchall()
    
    # Araçlar
    cursor.execute("""
        SELECT a.*, b.bayi_adi, b.sehir
        FROM araclar a
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        ORDER BY a.ilan_tarihi DESC
    """)
    araclar = cursor.fetchall()
    
    # Kullanıcılar
    cursor.execute("SELECT * FROM kullanicilar ORDER BY kayit_tarihi DESC")
    kullanicilar = cursor.fetchall()
    
    # Alım Talepleri
    cursor.execute("""
        SELECT aat.*, a.marka, a.model, a.yil, a.fiyat,
               b.bayi_adi, k.ad, k.soyad, k.email, k.telefon
        FROM arac_alim_talebi aat
        JOIN araclar a ON aat.arac_id = a.arac_id
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        JOIN kullanicilar k ON aat.musteri_id = k.kullanici_id
        ORDER BY aat.talep_tarihi DESC
    """)
    alim_talepleri = cursor.fetchall()
    
    # Satım Talepleri
    cursor.execute("""
        SELECT ast.*, b.bayi_adi, k.ad, k.soyad, k.email, k.telefon
        FROM arac_satim_talebi ast
        JOIN bayiler b ON ast.bayi_id = b.bayi_id
        JOIN kullanicilar k ON ast.musteri_id = k.kullanici_id
        ORDER BY ast.talep_tarihi DESC
    """)
    satim_talepleri = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('admin.html',
                         bayiler=bayiler,
                         araclar=araclar,
                         kullanicilar=kullanicilar,
                         alim_talepleri=alim_talepleri,
                         satim_talepleri=satim_talepleri)

# ============================================
# BAYİ PANEL - TEK SAYFA
# ============================================

@app.route('/bayi', methods=['GET', 'POST'])
def bayi():
    if 'kullanici_id' not in session or session['yetki'] != 'personel':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Bayi ID al
    cursor.execute("SELECT bayi_id FROM personeller WHERE kullanici_id=%s", (session['kullanici_id'],))
    bayi_info = cursor.fetchone()
    if not bayi_info:
        return redirect(url_for('logout'))
    bayi_id = bayi_info['bayi_id']
    
    # Araç ekleme
    if request.method == 'POST' and 'arac_ekle' in request.form:
        cursor.execute("""
            INSERT INTO araclar 
            (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, fiyat, plaka, arac_durumu, aciklama, ilan_tarihi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (bayi_id, request.form['marka'], request.form['model'], request.form['yil'],
              request.form['kilometre'], request.form['yakit'], request.form['vites'],
              request.form['renk'], request.form['fiyat'], request.form['plaka'],
              request.form['arac_durumu'], request.form.get('aciklama', '')))
        db.commit()
        flash('Araç eklendi!', 'success')
    
    # Personel ekleme
    if request.method == 'POST' and 'personel_ekle' in request.form:
        ad = request.form['ad']
        soyad = request.form['soyad']
        email = request.form['email']
        telefon = request.form['telefon']
        sifre = request.form['sifre']
        gorev = request.form['gorev']
        
        try:
            # Kullanıcı ekle
            cursor.execute("""
                INSERT INTO kullanicilar (ad, soyad, email, telefon, sifre, yetki, kayit_tarihi)
                VALUES (%s, %s, %s, %s, %s, 'personel', NOW())
            """, (ad, soyad, email, telefon, sifre))
            db.commit()
            
            # Yeni user ID'sini al
            kullanici_id = cursor.lastrowid
            
            # Personel tablosuna ekle
            cursor.execute("""
                INSERT INTO personeller (kullanici_id, bayi_id, gorev)
                VALUES (%s, %s, %s)
            """, (kullanici_id, bayi_id, gorev))
            db.commit()
            flash('Eleman başarıyla eklendi!', 'success')
        except:
            flash('Bu email zaten kullanılıyor!', 'error')
    
    # Talep durumu güncelleme (Alım)
    if request.method == 'POST' and 'alim_durum' in request.form:
        cursor.execute("UPDATE arac_alim_talebi SET durum=%s WHERE talep_id=%s",
                      (request.form['durum'], request.form['talep_id']))
        db.commit()
        flash('Talep güncellendi!', 'success')
    
    # Talep durumu güncelleme (Satım) + Stoğa ekleme
    if request.method == 'POST' and 'satim_durum' in request.form:
        durum = request.form['durum']
        talep_id = request.form['talep_id']
        
        # Eğer "Satın Alındı" ise stoğa ekle
        if durum == 'Satin Alindi':
            cursor.execute("SELECT * FROM arac_satim_talebi WHERE talep_id=%s", (talep_id,))
            talep = cursor.fetchone()
            
            # Müşteriden alınan aracı stoğa ekle
            cursor.execute("""
                INSERT INTO araclar 
                (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, fiyat, plaka, arac_durumu, aciklama, ilan_tarihi)
                VALUES (%s, %s, %s, %s, %s, 'Benzin', 'Manuel', 'Belirsiz', %s, 'YENİ', 'Satista', 'Müşteriden alınan araç', NOW())
            """, (bayi_id, talep['marka'], talep['model'], talep['yil'], 
                  talep['kilometre'], talep['fiyat_beklentisi']))
            db.commit()
            flash('Araç stoğa eklendi!', 'success')
        
        cursor.execute("UPDATE arac_satim_talebi SET durum=%s WHERE talep_id=%s", (durum, talep_id))
        db.commit()
        flash('Talep güncellendi!', 'success')
    
    # Bayi bilgileri
    cursor.execute("SELECT * FROM bayiler WHERE bayi_id=%s", (bayi_id,))
    bayi = cursor.fetchone()
    
    # Araçlar
    cursor.execute("SELECT * FROM araclar WHERE bayi_id=%s ORDER BY ilan_tarihi DESC", (bayi_id,))
    araclar = cursor.fetchall()
    
    # Personeller
    cursor.execute("""
        SELECT k.*, p.personel_id, p.gorev
        FROM personeller p
        JOIN kullanicilar k ON p.kullanici_id = k.kullanici_id
        WHERE p.bayi_id = %s
    """, (bayi_id,))
    personeller = cursor.fetchall()
    
    # Alım talepleri
    cursor.execute("""
        SELECT aat.*, a.marka, a.model, a.yil, a.fiyat, a.plaka,
               k.ad, k.soyad, k.email, k.telefon
        FROM arac_alim_talebi aat
        JOIN araclar a ON aat.arac_id = a.arac_id
        JOIN kullanicilar k ON aat.musteri_id = k.kullanici_id
        WHERE a.bayi_id = %s
        ORDER BY aat.talep_tarihi DESC
    """, (bayi_id,))
    alim_talepleri = cursor.fetchall()
    
    # Satım talepleri
    cursor.execute("""
        SELECT ast.*, k.ad, k.soyad, k.email, k.telefon
        FROM arac_satim_talebi ast
        JOIN kullanicilar k ON ast.musteri_id = k.kullanici_id
        WHERE ast.bayi_id = %s
        ORDER BY ast.talep_tarihi DESC
    """, (bayi_id,))
    satim_talepleri = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('bayi.html',
                         bayi=bayi,
                         araclar=araclar,
                         personeller=personeller,
                         alim_talepleri=alim_talepleri,
                         satim_talepleri=satim_talepleri)

# ============================================
# MÜŞTERİ PANEL - TEK SAYFA
# ============================================

@app.route('/musteri', methods=['GET', 'POST'])
def musteri():
    if 'kullanici_id' not in session or session['yetki'] != 'musteri':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Araç alım talebi oluşturma
    if request.method == 'POST' and 'alim_talep' in request.form:
        cursor.execute("""
            INSERT INTO arac_alim_talebi (musteri_id, arac_id, odeme_tipi, durum, notlar, talep_tarihi)
            VALUES (%s, %s, %s, 'Beklemede', %s, NOW())
        """, (session['kullanici_id'], request.form['arac_id'], 
              request.form['odeme_tipi'], request.form.get('notlar', '')))
        db.commit()
        flash('Alım talebi oluşturuldu!', 'success')
    
    # Araç satım talebi oluşturma
    if request.method == 'POST' and 'satim_talep' in request.form:
        cursor.execute("""
            INSERT INTO arac_satim_talebi 
            (musteri_id, bayi_id, marka, model, yil, kilometre, fiyat_beklentisi, ekspertiz, durum, talep_tarihi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Beklemede', NOW())
        """, (session['kullanici_id'], request.form['bayi_id'], request.form['marka'],
              request.form['model'], request.form['yil'], request.form['kilometre'],
              request.form['fiyat_beklentisi'], request.form['ekspertiz']))
        db.commit()
        flash('Satım talebi oluşturuldu!', 'success')
    
    # Satışta olan araçlar
    cursor.execute("""
        SELECT a.*, b.bayi_adi, b.sehir
        FROM araclar a
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        WHERE a.arac_durumu = 'Satista'
        ORDER BY a.ilan_tarihi DESC
    """)
    araclar = cursor.fetchall()
    
    # Bayiler
    cursor.execute("SELECT * FROM bayiler")
    bayiler = cursor.fetchall()
    
    # Alım talepleri
    cursor.execute("""
        SELECT aat.*, a.marka, a.model, a.yil, a.fiyat, b.bayi_adi
        FROM arac_alim_talebi aat
        JOIN araclar a ON aat.arac_id = a.arac_id
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        WHERE aat.musteri_id = %s
        ORDER BY aat.talep_tarihi DESC
    """, (session['kullanici_id'],))
    alim_talepleri = cursor.fetchall()
    
    # Satım talepleri
    cursor.execute("""
        SELECT ast.*, b.bayi_adi
        FROM arac_satim_talebi ast
        JOIN bayiler b ON ast.bayi_id = b.bayi_id
        WHERE ast.musteri_id = %s
        ORDER BY ast.talep_tarihi DESC
    """, (session['kullanici_id'],))
    satim_talepleri = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('musteri.html',
                         araclar=araclar,
                         bayiler=bayiler,
                         alim_talepleri=alim_talepleri,
                         satim_talepleri=satim_talepleri)

if __name__ == '__main__':
    app.run(debug=True, port=5000)