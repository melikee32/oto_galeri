from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this'

# Veritabanı bağlantı ayarları
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # XAMPP varsayılan şifre boş
    'database': 'oto_galeri'
}

def get_db():
    """Veritabanı bağlantısı oluşturur"""
    return mysql.connector.connect(**DB_CONFIG)

# ============================================
# ANA SAYFA VE LOGIN
# ============================================

@app.route('/')
def index():
    """Ana sayfa - Login olmamış kullanıcılar için"""
    if 'kullanici_id' in session:
        yetki = session.get('yetki')
        if yetki == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif yetki == 'personel':
            return redirect(url_for('bayi_dashboard'))
        elif yetki == 'musteri':
            return redirect(url_for('musteri_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if request.method == 'POST':
        email = request.form['email']
        sifre = request.form['sifre']
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM kullanicilar WHERE email = %s AND sifre = %s",
            (email, sifre)
        )
        kullanici = cursor.fetchone()
        cursor.close()
        db.close()
        
        if kullanici:
            session['kullanici_id'] = kullanici['kullanici_id']
            session['ad'] = kullanici['ad']
            session['soyad'] = kullanici['soyad']
            session['yetki'] = kullanici['yetki']
            
            flash('Başarıyla giriş yapıldı!', 'success')
            
            if kullanici['yetki'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif kullanici['yetki'] == 'personel':
                return redirect(url_for('bayi_dashboard'))
            elif kullanici['yetki'] == 'musteri':
                return redirect(url_for('musteri_dashboard'))
        else:
            flash('Email veya şifre hatalı!', 'error')
    
    return render_template('login.html')

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

@app.route('/logout')
def logout():
    """Çıkış yap"""
    session.clear()
    flash('Başarıyla çıkış yapıldı!', 'success')
    return redirect(url_for('login'))

# ============================================
# ADMIN PANEL
# ============================================

@app.route('/admin')
def admin_dashboard():
    """Admin ana sayfa"""
    if 'kullanici_id' not in session or session.get('yetki') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # İstatistikler
    cursor.execute("SELECT COUNT(*) as toplam FROM bayiler")
    bayi_sayisi = cursor.fetchone()['toplam']
    
    cursor.execute("SELECT COUNT(*) as toplam FROM araclar")
    arac_sayisi = cursor.fetchone()['toplam']
    
    cursor.execute("SELECT COUNT(*) as toplam FROM kullanicilar WHERE yetki='musteri'")
    musteri_sayisi = cursor.fetchone()['toplam']
    
    cursor.execute("SELECT COUNT(*) as toplam FROM arac_alim_talebi WHERE durum='Beklemede'")
    bekleyen_talepler = cursor.fetchone()['toplam']
    
    cursor.close()
    db.close()
    
    return render_template('admin/index.html',
                         bayi_sayisi=bayi_sayisi,
                         arac_sayisi=arac_sayisi,
                         musteri_sayisi=musteri_sayisi,
                         bekleyen_talepler=bekleyen_talepler)

# ============================================
# BAYİ PANEL
# ============================================

@app.route('/bayi')
def bayi_dashboard():
    """Bayi personel ana sayfa"""
    if 'kullanici_id' not in session or session.get('yetki') != 'personel':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Personelin bağlı olduğu bayi
    cursor.execute("""
        SELECT b.* FROM bayiler b
        JOIN personeller p ON b.bayi_id = p.bayi_id
        WHERE p.kullanici_id = %s
    """, (session['kullanici_id'],))
    bayi = cursor.fetchone()
    
    if not bayi:
        flash('Personel kaydınız bulunamadı!', 'error')
        return redirect(url_for('logout'))
    
    bayi_id = bayi['bayi_id']
    
    # İstatistikler
    cursor.execute("SELECT COUNT(*) as toplam FROM araclar WHERE bayi_id = %s", (bayi_id,))
    arac_sayisi = cursor.fetchone()['toplam']
    
    cursor.execute("""
        SELECT COUNT(*) as toplam FROM arac_alim_talebi aat
        JOIN araclar a ON aat.arac_id = a.arac_id
        WHERE a.bayi_id = %s AND aat.durum = 'Beklemede'
    """, (bayi_id,))
    bekleyen_alim = cursor.fetchone()['toplam']
    
    cursor.execute("""
        SELECT COUNT(*) as toplam FROM arac_satim_talebi
        WHERE bayi_id = %s AND durum = 'Beklemede'
    """, (bayi_id,))
    bekleyen_satim = cursor.fetchone()['toplam']
    
    cursor.close()
    db.close()
    
    return render_template('bayi/index.html',
                         bayi=bayi,
                         arac_sayisi=arac_sayisi,
                         bekleyen_alim=bekleyen_alim,
                         bekleyen_satim=bekleyen_satim)

# ============================================
# ADMIN - BAYİLER YÖNETİMİ
# ============================================

@app.route('/admin/bayiler')
def admin_bayiler():
    """Admin - Bayileri listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
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
    
    cursor.close()
    db.close()
    
    return render_template('admin/bayiler.html', bayiler=bayiler)

# ============================================
# ADMIN - ARAÇLAR YÖNETİMİ
# ============================================

@app.route('/admin/araclar')
def admin_araclar():
    """Admin - Tüm araçları listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.*, b.bayi_adi, b.sehir
        FROM araclar a
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        ORDER BY a.ilan_tarihi DESC
    """)
    araclar = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('admin/araclar.html', araclar=araclar)

# ============================================
# ADMIN - KULLANICILAR YÖNETİMİ
# ============================================

@app.route('/admin/kullanicilar')
def admin_kullanicilar():
    """Admin - Kullanıcıları listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM kullanicilar ORDER BY kayit_tarihi DESC")
    kullanicilar = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('admin/kullanicilar.html', kullanicilar=kullanicilar)

# ============================================
# ADMIN - TALEPLER YÖNETİMİ
# ============================================

@app.route('/admin/talepler')
def admin_talepler():
    """Admin - Tüm talepleri listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Alım talepleri
    cursor.execute("""
        SELECT aat.*, 
               a.marka, a.model, a.yil, a.fiyat,
               b.bayi_adi,
               k.ad, k.soyad, k.email, k.telefon
        FROM arac_alim_talebi aat
        JOIN araclar a ON aat.arac_id = a.arac_id
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        JOIN kullanicilar k ON aat.musteri_id = k.kullanici_id
        ORDER BY aat.talep_tarihi DESC
    """)
    alim_talepleri = cursor.fetchall()
    
    # Satım talepleri
    cursor.execute("""
        SELECT ast.*,
               b.bayi_adi,
               k.ad, k.soyad, k.email, k.telefon
        FROM arac_satim_talebi ast
        JOIN bayiler b ON ast.bayi_id = b.bayi_id
        JOIN kullanicilar k ON ast.musteri_id = k.kullanici_id
        ORDER BY ast.talep_tarihi DESC
    """)
    satim_talepleri = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('admin/talepler.html', 
                         alim_talepleri=alim_talepleri,
                         satim_talepleri=satim_talepleri)

# ============================================
# BAYİ - ARAÇLAR YÖNETİMİ
# ============================================

@app.route('/bayi/araclar')
def bayi_araclar():
    """Bayi - Kendi araçlarını listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'personel':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Personelin bayi ID'sini al
    cursor.execute("""
        SELECT bayi_id FROM personeller 
        WHERE kullanici_id = %s
    """, (session['kullanici_id'],))
    result = cursor.fetchone()
    
    if not result:
        flash('Personel kaydınız bulunamadı!', 'error')
        return redirect(url_for('logout'))
    
    bayi_id = result['bayi_id']
    
    # Bayinin araçlarını getir
    cursor.execute("""
        SELECT * FROM araclar 
        WHERE bayi_id = %s
        ORDER BY ilan_tarihi DESC
    """, (bayi_id,))
    araclar = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('bayi/araclar.html', araclar=araclar)

@app.route('/bayi/arac-ekle', methods=['GET', 'POST'])
def bayi_arac_ekle():
    """Bayi - Yeni araç ekle"""
    if 'kullanici_id' not in session or session.get('yetki') != 'personel':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Personelin bayi ID'sini al
        cursor.execute("""
            SELECT bayi_id FROM personeller 
            WHERE kullanici_id = %s
        """, (session['kullanici_id'],))
        result = cursor.fetchone()
        bayi_id = result['bayi_id']
        
        # Form verilerini al
        marka = request.form['marka']
        model = request.form['model']
        yil = request.form['yil']
        kilometre = request.form['kilometre']
        yakit = request.form['yakit']
        vites = request.form['vites']
        renk = request.form['renk']
        fiyat = request.form['fiyat']
        plaka = request.form['plaka']
        arac_durumu = request.form['arac_durumu']
        aciklama = request.form.get('aciklama', '')
        
        # Veritabanına ekle
        cursor.execute("""
            INSERT INTO araclar 
            (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, 
             fiyat, plaka, arac_durumu, aciklama, ilan_tarihi)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (bayi_id, marka, model, yil, kilometre, yakit, vites, renk, 
              fiyat, plaka, arac_durumu, aciklama))
        
        db.commit()
        cursor.close()
        db.close()
        
        flash('Araç başarıyla eklendi!', 'success')
        return redirect(url_for('bayi_araclar'))
    
    return render_template('bayi/arac_ekle.html')

# ============================================
# BAYİ - ALIM TALEPLERİ
# ============================================

@app.route('/bayi/alim-talepleri')
def bayi_alim_talepleri():
    """Bayi - Alım taleplerini listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'personel':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Personelin bayi ID'sini al
    cursor.execute("""
        SELECT bayi_id FROM personeller 
        WHERE kullanici_id = %s
    """, (session['kullanici_id'],))
    result = cursor.fetchone()
    bayi_id = result['bayi_id']
    
    # Alım taleplerini getir
    cursor.execute("""
        SELECT aat.*, 
               a.marka, a.model, a.yil, a.fiyat, a.plaka,
               k.ad, k.soyad, k.email, k.telefon
        FROM arac_alim_talebi aat
        JOIN araclar a ON aat.arac_id = a.arac_id
        JOIN kullanicilar k ON aat.musteri_id = k.kullanici_id
        WHERE a.bayi_id = %s
        ORDER BY aat.talep_tarihi DESC
    """, (bayi_id,))
    talepler = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('bayi/alim_talepleri.html', talepler=talepler)

@app.route('/bayi/alim-talep-duzenle/<int:talep_id>', methods=['POST'])
def bayi_alim_talep_duzenle(talep_id):
    """Bayi - Alım talebi durumunu güncelle"""
    if 'kullanici_id' not in session or session.get('yetki') != 'personel':
        return redirect(url_for('login'))
    
    durum = request.form['durum']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE arac_alim_talebi 
        SET durum = %s 
        WHERE talep_id = %s
    """, (durum, talep_id))
    db.commit()
    cursor.close()
    db.close()
    
    flash('Talep durumu güncellendi!', 'success')
    return redirect(url_for('bayi_alim_talepleri'))

# ============================================
# BAYİ - SATIM TALEPLERİ
# ============================================

@app.route('/bayi/satim-talepleri')
def bayi_satim_talepleri():
    """Bayi - Satım taleplerini listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'personel':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Personelin bayi ID'sini al
    cursor.execute("""
        SELECT bayi_id FROM personeller 
        WHERE kullanici_id = %s
    """, (session['kullanici_id'],))
    result = cursor.fetchone()
    bayi_id = result['bayi_id']
    
    # Satım taleplerini getir
    cursor.execute("""
        SELECT ast.*,
               k.ad, k.soyad, k.email, k.telefon
        FROM arac_satim_talebi ast
        JOIN kullanicilar k ON ast.musteri_id = k.kullanici_id
        WHERE ast.bayi_id = %s
        ORDER BY ast.talep_tarihi DESC
    """, (bayi_id,))
    talepler = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('bayi/satim_talepleri.html', talepler=talepler)

@app.route('/bayi/satim-talep-duzenle/<int:talep_id>', methods=['POST'])
def bayi_satim_talep_duzenle(talep_id):
    """Bayi - Satım talebi durumunu güncelle"""
    if 'kullanici_id' not in session or session.get('yetki') != 'personel':
        return redirect(url_for('login'))
    
    durum = request.form['durum']
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE arac_satim_talebi 
        SET durum = %s 
        WHERE talep_id = %s
    """, (durum, talep_id))
    db.commit()
    cursor.close()
    db.close()
    
    flash('Talep durumu güncellendi!', 'success')
    return redirect(url_for('bayi_satim_talepleri'))

# ============================================
# MÜŞTERİ PANEL
# ============================================

@app.route('/musteri')
def musteri_dashboard():
    """Müşteri ana sayfa"""
    if 'kullanici_id' not in session or session.get('yetki') != 'musteri':
        flash('Bu sayfaya erişim yetkiniz yok!', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Satışta olan araçlar
    cursor.execute("""
        SELECT a.*, b.bayi_adi, b.sehir
        FROM araclar a
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        WHERE a.arac_durumu = 'Satista'
        ORDER BY a.ilan_tarihi DESC
        LIMIT 6
    """)
    araclar = cursor.fetchall()
    
    # Müşterinin talepleri
    cursor.execute("""
        SELECT COUNT(*) as toplam FROM arac_alim_talebi
        WHERE musteri_id = %s
    """, (session['kullanici_id'],))
    alim_talebi_sayisi = cursor.fetchone()['toplam']
    
    cursor.execute("""
        SELECT COUNT(*) as toplam FROM arac_satim_talebi
        WHERE musteri_id = %s
    """, (session['kullanici_id'],))
    satim_talebi_sayisi = cursor.fetchone()['toplam']
    
    cursor.close()
    db.close()
    
    return render_template('musteri/index.html',
                         araclar=araclar,
                         alim_talebi_sayisi=alim_talebi_sayisi,
                         satim_talebi_sayisi=satim_talebi_sayisi)

@app.route('/musteri/araclar')
def musteri_araclar():
    """Müşteri - Tüm araçları listele"""
    if 'kullanici_id' not in session or session.get('yetki') != 'musteri':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.*, b.bayi_adi, b.sehir
        FROM araclar a
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        WHERE a.arac_durumu = 'Satista'
        ORDER BY a.ilan_tarihi DESC
    """)
    araclar = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('musteri/araclar.html', araclar=araclar)

@app.route('/musteri/talep-olustur/<int:arac_id>', methods=['GET', 'POST'])
def musteri_talep_olustur(arac_id):
    """Müşteri - Araç alım talebi oluştur"""
    if 'kullanici_id' not in session or session.get('yetki') != 'musteri':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        odeme_tipi = request.form['odeme_tipi']
        notlar = request.form['notlar']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO arac_alim_talebi
            (musteri_id, arac_id, odeme_tipi, durum, notlar, talep_tarihi)
            VALUES (%s, %s, %s, 'Beklemede', %s, NOW())
        """, (session['kullanici_id'], arac_id, odeme_tipi, notlar))
        db.commit()
        cursor.close()
        db.close()
        
        flash('Talebiniz başarıyla oluşturuldu!', 'success')
        return redirect(url_for('musteri_taleplerim'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, b.bayi_adi
        FROM araclar a
        JOIN bayiler b ON a.bayi_id = b.bayi_id
        WHERE a.arac_id = %s
    """, (arac_id,))
    arac = cursor.fetchone()
    cursor.close()
    db.close()
    
    return render_template('musteri/talep_olustur.html', arac=arac)

@app.route('/musteri/taleplerim')
def musteri_taleplerim():
    """Müşteri - Taleplerim"""
    if 'kullanici_id' not in session or session.get('yetki') != 'musteri':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
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
    
    return render_template('musteri/taleplerim.html',
                         alim_talepleri=alim_talepleri,
                         satim_talepleri=satim_talepleri)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)