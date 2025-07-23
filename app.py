from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from werkzeug.utils import secure_filename
import tempfile
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# .env dosyasından API anahtarını yükle
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Eğer .env dosyasından okunamazsa, doğrudan buraya yazabilirsiniz
if not GOOGLE_API_KEY:
    # API anahtarınızı buraya yazın (geçici çözüm)
    GOOGLE_API_KEY = "your_api_key_here"  # Buraya gerçek API anahtarınızı yazın
    
if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_api_key_here":
    print("⚠️  UYARI: GOOGLE_API_KEY bulunamadı. Yapay zeka özellikleri devre dışı.")
    print("📝 Çözüm: Yukarıdaki satıra gerçek API anahtarınızı yazın")
    GOOGLE_API_KEY = None

# Gemini AI yapılandırması (Gemini 2.0 Flash)
model = None
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test mesajı gönder
        response = model.generate_content("Merhaba, nasılsın?")
        print("✅ Yapay Zeka Başarıyla Başlatıldı")
    except Exception as e:
        print(f"❌ Yapay Zeka Hatası: {str(e)}")
        model = None
else:
    print("⚠️  Yapay Zeka Devre Dışı - API Anahtarı Gerekli")

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'  # Güvenlik için değiştirin
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///unibot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Veritabanı Modelleri
class LibraryInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CafeteriaInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=True)  # Eski sistem için opsiyonel
    date = db.Column(db.Date, nullable=False)  # Yeni: Her gün için tarih
    menu = db.Column(db.Text, nullable=False)
    hours = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RegistrationInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ShuttleInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Veritabanını oluştur ve verileri ekle
def init_db():
    with app.app_context():
        # Önce tüm tabloları sil
        db.drop_all()
        # Sonra tabloları yeniden oluştur
        db.create_all()
        
        # Kütüphane bilgilerini ekle
        library_info = [
            {'category': 'saatler', 'content': "Kütüphane Çalışma Saatleri:\n- Hafta İçi: 08:00-22:00\n- Hafta Sonu: 09:00-17:00\n- Sınav Dönemi: 24 saat açık"},
            {'category': 'kurallar', 'content': "Kütüphane Kuralları:\n- Sessiz çalışma zorunludur\n- Yiyecek/içecek yasaktır\n- Kitap ödünç süresi 15 gündür"},
            {'category': 'genel', 'content': "Kütüphane Hizmetleri:\n- Online katalog tarama\n- Grup çalışma odaları\n- Dijital kütüphane erişimi\n- Fotokopi ve tarama"}
        ]
        
        for info in library_info:
            if not LibraryInfo.query.filter_by(category=info['category']).first():
                db.session.add(LibraryInfo(**info))
        
        # Yemekhane bilgilerini ekle (Mayıs 2025)
        import datetime
        mayis_2025_menuleri = [
            # (tarih, menü)
            (datetime.date(2025, 5, 1), 'Resmi Tatil'),
            (datetime.date(2025, 5, 2), 'Yayla Çorba\nÇiftlik Köfte\nBeşamel Soslu Makarna\nVişne Komposto'),
            (datetime.date(2025, 5, 5), 'Tarhana Çorba\nFırın Tavuk/Acılı Ezme\nBeşamel Soslu Makarna\nMevsim Salata'),
            (datetime.date(2025, 5, 6), 'Toyga Çorba\nSalçalı Köfte\nYoğurtlu Mantı\nMeyve'),
            (datetime.date(2025, 5, 7), 'Mercimek Çorba\nTas Kebabı\nNohutlu Pirinç Pilavı\nAyran'),
            (datetime.date(2025, 5, 8), 'Resmi Tatil'),
            (datetime.date(2025, 5, 9), 'Düğün Çorba\nMevsim Türlü\nCevizli Erişte\nIslak Kek'),
            (datetime.date(2025, 5, 12), 'Tarhana Çorba\nKıymalı Patates Yemeği\nSu Böreği\nSütlaç'),
            (datetime.date(2025, 5, 13), 'Sebze Çorba\nİzmir Köfte\nCevizli Erişte\nMevsim Salata'),
            (datetime.date(2025, 5, 14), 'Tavuklu Sultan Çorba\nKuru Fasulye\nŞehriyeli Pirinç Pilavı\nTrileçe'),
            (datetime.date(2025, 5, 15), 'Domates Çorba\nÇoban Kavurma\nNohutlu Bulgur Pilavı\nAyran'),
            (datetime.date(2025, 5, 16), 'Ezogelin Çorba\nTavuk Döner/Acılı Ezme\nNapoliten Soslu Makarna\nMevsim Salata'),
            (datetime.date(2025, 5, 19), 'Resmi Tatil'),
            (datetime.date(2025, 5, 20), 'Düğün Çorba\nTaze Fasulye\nKol Böreği\nSoğuk Baklava'),
            (datetime.date(2025, 5, 21), 'Mahulta Çorba\nTavuk Sote\nNapoliten Soslu Makarna\nMeyve'),
            (datetime.date(2025, 5, 22), 'Romen Çorba\nNohut\nBulgur Pilavı\nAyran'),
            (datetime.date(2025, 5, 23), 'Mercimek Çorba\nOrman Kebabı\nŞehriyeli Pirinç Pilavı\nSakızlı Muhallebi'),
            (datetime.date(2025, 5, 26), 'Tarhana Çorba\nBiber Dolma/Yoğurt\nSoslu Mantı\nSütlü Bükme'),
            (datetime.date(2025, 5, 27), 'Tavuk Suyu Çorba\nBarbunya\nPirinç Pilavı\nRevani'),
            (datetime.date(2025, 5, 28), 'Kremalı Sebze Çorba\nPiliç Nugget/ketçap,mayonez\nNapoliten Soslu Makarna\nAyran'),
            (datetime.date(2025, 5, 29), 'Ezogelin Çorba\nPideli Köfte\nCevizli Erişte\nYoğurt'),
            (datetime.date(2025, 5, 30), 'Mercimek Çorba\nEt Sote\nŞehriyeli Pirinç Pilavı\nMevsim Salata'),
        ]
        
        for tarih, menu in mayis_2025_menuleri:
            db.session.add(CafeteriaInfo(date=tarih, menu=menu, hours="Öğle: 11:30-14:00\nAkşam: 16:30-19:00", price="30 TL"))
        
        # Kayıt bilgilerini ekle
        registration_content = "Kayıt İşlemleri:\n\nTarihler:\n- Kayıt Yenileme: 08-12 Eylül 2025 \n- Harç Son Ödeme: 12 Eylül 2025\n- Ders Seçimi:  08-12 Eylül 2025\n\nGerekli Belgeler:\n- Öğrenci Belgesi\n- Harç Dekontu\n- Ders Seçim Formu\n\nNot: Tüm işlemler OBS üzerinden yapılacaktır."
        if not RegistrationInfo.query.first():
            db.session.add(RegistrationInfo(content=registration_content))
        
        # Servis bilgilerini ekle
        shuttle_content = "Ulaşım Servisleri:\n\nSaatler:\n- İlk Sefer: 08:00\n- Son Sefer: 23:00\n- Sefer Sıklığı: Her saat başı\n\nGüzergahlar:\n1. Hat: Merkez - Hastane\n2. Hat: Merkez - Terminal\n3. Hat: Kampüs İçi\n\nNot: Servisler öğrenci ücreti 17 tl'dir."
        if not ShuttleInfo.query.first():
            db.session.add(ShuttleInfo(content=shuttle_content))
        
        db.session.commit()

# Veritabanını başlat
init_db()

# BŞEÜ Sıkça Sorulan Sorular veritabanı
RULES_DB = {
    # Kısayol Komutları
    "!kütüphane": "Kütüphane bilgileri için:\n- !kütüphane saatleri\n- !kütüphane kuralları\n- !kütüphane genel",
    "!kütüphane saatleri": "Kütüphane Çalışma Saatleri:\n- Hafta İçi: 08:00-22:00\n- Hafta Sonu: 09:00-17:00\n- Sınav Dönemi: 24 saat açık",
    "!kütüphane kuralları": "Kütüphane Kuralları:\n- Sessiz çalışma zorunludur\n- Yiyecek/içecek yasaktır\n- Kitap ödünç süresi 15 gündür",
    "!kütüphane genel": "Kütüphane Hizmetleri:\n- Online katalog tarama\n- Grup çalışma odaları\n- Dijital kütüphane erişimi\n- Fotokopi ve tarama",
    
    "!yemek": "Yemekhane bilgileri için:\n- !yemek menü\n- !yemek saatler\n- !yemek fiyat",
    "!yemek menü": "Günlük menü bilgisi için yemekhane panolarını veya üniversite web sitesini kontrol edebilirsiniz.",
    "!yemek saatler": "Yemekhane Saatleri:\n- Öğle: 11:30-14:00\n- Akşam: 15:00-19:00",
    "!yemek fiyat": "Öğrenci Fiyatı: 30 TL",
    
    "!kayıt": "Kayıt İşlemleri:\n\nTarihler:\n- Kayıt Yenileme:  08-12 Eylül 2025\n- Harç Son Ödeme:12 Eylül 2025\n- Ders Seçimi: 08-12 Eylül 2025\n\nGerekli Belgeler:\n- Öğrenci Belgesi\n- Harç Dekontu\n- Ders Seçim Formu\n\nNot: Tüm işlemler OBS üzerinden yapılacaktır.",
    
    "!servis": "Ulaşım Servisleri:\n\nSaatler:\n- İlk Sefer: 08:00\n- Son Sefer: 23:00\n- Sefer Sıklığı: Her saat başı\n\nGüzergahlar:\n1. Hat: Merkez - Hastane\n2. Hat: Merkez - Terminal\n3. Hat: Kampüs İçi\n\nNot: Servisler öğrenci ücreti 17 tl'dir.",
    
    # Anlık Duyurular
    "!duyuru": "Güncel Duyurular:\n\n1. Kayıt Yenileme:  08-12 Eylül 2025\n2. Harç Son Ödeme:12 Eylül 2025\n3. Ders Seçimi: 08-12 Eylül 2025\n4. Güz Dönemi Başlangıcı: 15 Eylül 2025\n\nDetaylı bilgi için: https://ogrenci.bilecik.edu.tr",
    "!anlık duyuru": "Güncel Duyurular:\n\n1. Kayıt Yenileme: 08-12 Eylül 2025\n2. Harç Son Ödeme:12 Eylül 2025\n3. Ders Seçimi: 08-12 Eylül 2025\n4. Güz Dönemi Başlangıcı: 15 Eylül 2025\n\nDetaylı bilgi için: https://ogrenci.bilecik.edu.tr",
    
    # Harç İşlemleri
    "!harç": "Harç işlemleri hakkında bilgi almak için Öğrenci İşleri Daire Başkanlığı'na başvurabilirsiniz. Harç ödemeleri ve muafiyet işlemleri için gerekli belgeleri yanınızda bulundurmanız gerekmektedir.",
    "!harçödeme": "Harç ödemeleri banka üzerinden yapılmaktadır. Ödeme tarihleri ve detayları için Öğrenci İşleri Daire Başkanlığı'nın web sitesini kontrol edebilirsiniz.",
    "!harçmuaf": "Harç muafiyeti için gerekli belgeler ve başvuru koşulları hakkında bilgi almak için Öğrenci İşleri Daire Başkanlığı'na başvurabilirsiniz.",
    
    # Akıllı Kart İşlemleri
    "!kart": "Akıllı kart işlemleri için Öğrenci İşleri Daire Başkanlığı'na başvurmanız gerekmektedir. Kart yenileme, kayıp durumunda yeni kart çıkarma işlemleri bu birimde yapılmaktadır.",
    "!kartkayıp": "Akıllı kartınızı kaybettiyseniz, Öğrenci İşleri Daire Başkanlığı'na başvurarak yeni kart çıkarma işlemi yapabilirsiniz.",
    "!kartyenile": "Akıllı kart yenileme işlemleri için Öğrenci İşleri Daire Başkanlığı'na başvurmanız gerekmektedir.",
    
    # İletişim Bilgileri
    "!iletişim": "Öğrenci İşleri Daire Başkanlığı iletişim bilgileri:\nAdres: Gülümbe Kampüsü 11230-BİLECİK\nTelefon: 0228 214 10 71\nE-posta: ogrenciisleri@bilecik.edu.tr",
    "!tel": "Öğrenci İşleri Daire Başkanlığı telefon numarası: 0228 214 10 71",
    "!adres": "Öğrenci İşleri Daire Başkanlığı adresi: Gülümbe Kampüsü 11230-BİLECİK",
    "!mail": "Öğrenci İşleri Daire Başkanlığı e-posta adresi: ogrenciisleri@bilecik.edu.tr",
    
    # Genel Bilgiler
    "!yardım": "Kullanılabilir kısayollar:\n1. Kütüphane: !kütüphane, !kütüphane saatleri, !kütüphane kuralları, !kütüphane genel\n2. Yemekhane: !yemek, !yemek menü, !yemek saatler, !yemek fiyat\n3. Kayıt: !kayıt\n4. Servis: !servis\n5. Duyurular: !duyuru, !anlık duyuru\n6. Harç İşlemleri: !harç, !harçödeme, !harçmuaf\n7. Akıllı Kart: !kart, !kartkayıp, !kartyenile\n8. İletişim: !iletişim, !tel, !adres, !mail\n9. Genel: !yardım, !merhaba",
    "!merhaba": "Merhaba! Ben Bilecik Şeyh Edebali Üniversitesi Öğrenci İşleri asistanıyım. Size nasıl yardımcı olabilirim? Kısayolları görmek için !yardım yazabilirsiniz.",
    "!teşekkür": "Rica ederim! Başka bir konuda yardıma ihtiyacınız olursa sormaktan çekinmeyin.",
    "!güle güle": "İyi günler dilerim! Başka bir sorunuz olursa tekrar beklerim.",
}

# kullanıcı veritabanı (kullanıcı adı/e-posta ve şifre)
USERS = {
    'ogrenci1': {'email': 'ogrenci1@bilecik.edu.tr', 'password': '123456'},
    'ogrenci2': {'email': 'ogrenci2@bilecik.edu.tr', 'password': '654321'},
    'Berivan Özdemir': {'email': '123456@ogrenci.bilecik.edu.tr', 'password': 'B****21'},
     'Beyzanur Termisin': {'email': '12456@ogrenci.bilecik.edu.tr', 'password': 'B****123'},
}

def get_rule_based_response(message):
    message = message.lower()
    # Tam eşleşme kontrolü
    if message in RULES_DB:
        return RULES_DB[message]
    
    # Kısmi eşleşme kontrolü
    for key in RULES_DB:
        if key in message:
            return RULES_DB[key]
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Kullanıcı adı veya e-posta ile giriş
        for user, info in USERS.items():
            if (username == user or username == info['email']) and password == info['password']:
                session['user'] = user
                return redirect(url_for('home'))
        return render_template('login.html', error='Kullanıcı adı veya şifre hatalı!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').lower()
    
    # Önce BŞEÜ SSS veritabanında ara
    rule_response = get_rule_based_response(message)
    if rule_response:
        return jsonify({'response': rule_response})
    
    # Kütüphane bilgileri
    if 'kütüphane' in message:
        if 'saat' in message:
            info = LibraryInfo.query.filter_by(category='saatler').first()
            return jsonify({'response': info.content if info else 'Kütüphane saatleri bilgisi bulunamadı.'})
        elif 'kural' in message:
            info = LibraryInfo.query.filter_by(category='kurallar').first()
            return jsonify({'response': info.content if info else 'Kütüphane kuralları bilgisi bulunamadı.'})
        else:
            info = LibraryInfo.query.filter_by(category='genel').first()
            return jsonify({'response': info.content if info else 'Kütüphane bilgisi bulunamadı.'})
    
    # Yemekhane bilgileri
    if 'yemek' in message or 'menü' in message or 'yemekhane' in message:
        today = datetime.now().date()
        info = CafeteriaInfo.query.filter_by(date=today).first()
        if info:
            response = f"{today.strftime('%d.%m.%Y')} Menüsü:\n{info.menu}\n\n{info.hours}\n\nÖğrenci Fiyatı: {info.price}"
            return jsonify({'response': response})
        return jsonify({'response': 'Bugüne ait yemekhane menüsü bulunamadı.'})
    
    # Kayıt bilgileri
    if 'kayıt' in message:
        info = RegistrationInfo.query.first()
        return jsonify({'response': info.content if info else 'Kayıt bilgileri bulunamadı.'})
    
    # Servis bilgileri
    if 'servis' in message or 'ulaşım' in message:
        info = ShuttleInfo.query.first()
        return jsonify({'response': info.content if info else 'Servis bilgileri bulunamadı.'})
    
    # Anlık duyurular
    if 'duyuru' in message or 'anlık' in message:
        return jsonify({'response': "Güncel Duyurular:\n\n1. Kayıt Yenileme: 1-15 Şubat 2024\n2. Harç Son Ödeme: 14 Şubat 2024\n3. Ders Seçimi: 1-15 Şubat 2024\n4. Bahar Dönemi Başlangıcı: 15 Eylül 2025\n\nDetaylı bilgi için: https://ogrenci.bilecik.edu.tr"})
    
    # Tarihçe ve genel bilgi soruları için yapay zeka kullanımı
    if any(keyword in message for keyword in ['tarihçe', 'kuruluş', 'kuruldu', 'hakkında', 'bilgi', 'nedir', 'kimdir']):
        try:
            system_prompt = (
                "Sen Bilecik Şeyh Edebali Üniversitesi Öğrenci İşleri asistanısın. Cevaplarını resmi, bilgilendirici ve üniversiteye uygun şekilde, kısa ve net olarak ver. "
                "Üniversite hakkında genel bilgiler:\n"
                "- Kuruluş: 2007 yılında kurulmuştur\n"
                "- Konum: Bilecik'in merkez ilçesinde bulunmaktadır\n"
                "- Kampüs: Gülümbe Kampüsü ana yerleşkedir\n"
                "- Fakülteler: Mühendislik, İİBF, Fen-Edebiyat, İlahiyat, Sağlık Bilimleri\n"
                "- Yüksekokullar: MYO, Sağlık MYO\n"
                "- Enstitüler: Lisansüstü Eğitim Enstitüsü\n"
                "Eğer bir cevapta iletişim bilgisi, web sitesi veya e-posta adresi gerekiyorsa aşağıdaki bilgileri kullan:\n"
                "- Web sitesi: https://ogrenci.bilecik.edu.tr\n"
                "- E-posta: ogrenciisleri@bilecik.edu.tr\n"
                "- Telefon: 0228 214 10 71\n"
                "- Adres: Gülümbe Kampüsü 11230-BİLECİK\n"
                "Bilmediğin veya üniversiteyle ilgisi olmayan sorulara 'Bu konuda yardımcı olamıyorum.' de."
            )
            response = model.generate_content([
                {'text': system_prompt},
                {'text': message}
            ])
            if response and hasattr(response, 'text'):
                return jsonify({'response': response.text})
        except Exception as e:
            print(f"Gemini API hatası: {str(e)}")
    
    # Eğer model yapılandırılamadıysa
    if model is None:
        return jsonify({'response': 'Üzgünüm, şu anda yapay zeka servisine erişemiyorum. Lütfen daha sonra tekrar deneyin.'})
    
    try:
        # Gemini'ye üniversite asistanı gibi cevap vermesi için sistem promptu ile sor
        system_prompt = (
            "Sen Bilecik Şeyh Edebali Üniversitesi Öğrenci İşleri asistanısın. Cevaplarını resmi, bilgilendirici ve üniversiteye uygun şekilde, kısa ve net olarak ver. "
            "Eğer bir cevapta iletişim bilgisi, web sitesi veya e-posta adresi gerekiyorsa aşağıdaki bilgileri kullan:\n"
            "- Web sitesi: https://ogrenci.bilecik.edu.tr\n"
            "- E-posta: ogrenciisleri@bilecik.edu.tr\n"
            "- Telefon: 0228 214 10 71\n"
            "- Adres: Gülümbe Kampüsü 11230-BİLECİK\n"
            "Bilmediğin veya üniversiteyle ilgisi olmayan sorulara 'Bu konuda yardımcı olamıyorum.' de."
        )
        response = model.generate_content([
            {'text': system_prompt},
            {'text': message}
        ])
        if response and hasattr(response, 'text'):
            return jsonify({'response': response.text})
        else:
            return jsonify({'response': 'Üzgünüm, yapay zeka servisinden yanıt alamadım. Lütfen daha sonra tekrar deneyin.'})
    except Exception as e:
        print(f"Gemini API hatası: {str(e)}")
        return jsonify({'response': 'Üzgünüm, şu anda yapay zeka servisine erişemiyorum. Lütfen daha sonra tekrar deneyin.'})

# Resimden yazı okuma (OCR) endpointi
@app.route('/image-to-text', methods=['POST'])
def image_to_text():
    if 'image' not in request.files:
        return jsonify({'response': 'Resim dosyası bulunamadı.'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'response': 'Lütfen bir resim dosyası seçin.'}), 400
    
    try:
        # Dosyayı geçici olarak kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp:
            file.save(temp.name)
            temp_path = temp.name
        
        # Gemini Flash ile görselden metin çıkar
        with open(temp_path, 'rb') as img_file:
            image_bytes = img_file.read()
            response = model.generate_content([
                {'mime_type': 'image/png', 'data': image_bytes},
                {'text': 'Bu görseldeki yazıyı oku ve sadece metni döndür. Eğer görselde yazı yoksa "Görselde yazı bulunamadı." yaz.'}
            ])
        
        os.remove(temp_path)  # Geçici dosyayı sil
        
        if response and hasattr(response, 'text'):
            ocr_text = response.text.strip()
            
            # Eğer görselde yazı yoksa
            if "Görselde yazı bulunamadı" in ocr_text:
                return jsonify({'response': 'Görselde okunabilir bir yazı bulunamadı.'})
            
            # Önce kural tabanlı veritabanında ara
            rule_response = get_rule_based_response(ocr_text)
            if rule_response:
                return jsonify({'response': rule_response})
            
            # Yoksa Gemini ile cevap üret
            system_prompt = (
                "Sen Bilecik Şeyh Edebali Üniversitesi Öğrenci İşleri asistanısın. "
                "Cevaplarını resmi, bilgilendirici ve üniversiteye uygun şekilde, kısa ve net olarak ver. "
                "Eğer bir cevapta iletişim bilgisi, web sitesi veya e-posta adresi gerekiyorsa aşağıdaki bilgileri kullan:\n"
                "- Web sitesi: https://ogrenci.bilecik.edu.tr\n"
                "- E-posta: ogrenciisleri@bilecik.edu.tr\n"
                "- Telefon: 0228 214 10 71\n"
                "- Adres: Gülümbe Kampüsü 11230-BİLECİK\n"
                "Bilmediğin veya üniversiteyle ilgisi olmayan sorulara 'Bu konuda yardımcı olamıyorum.' de."
            )
            
            ai_response = model.generate_content([
                {'text': system_prompt},
                {'text': ocr_text}
            ])
            
            if ai_response and hasattr(ai_response, 'text'):
                return jsonify({'response': ai_response.text})
            else:
                return jsonify({'response': 'Üzgünüm, görseldeki yazıya uygun cevap bulunamadı.'})
        else:
            return jsonify({'response': 'Üzgünüm, görselden metin okunamadı.'})
            
    except Exception as e:
        print(f"OCR/Gemini hata: {str(e)}")
        return jsonify({'response': 'Üzgünüm, görselden metin okunurken bir hata oluştu.'}), 500

if __name__ == '__main__':
    app.run(debug=True) 