import os

class Config:
    """Uygulama konfigürasyonu"""
    
    # Flask ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    DEBUG = True
    
    # Veritabanı ayarları
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''  # XAMPP için boş
    DB_NAME = 'oto_galeri'
    
    # Session ayarları
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 saat
    
    # Upload ayarları (gelecekte fotoğraf yüklemek için)
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max dosya boyutu
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}