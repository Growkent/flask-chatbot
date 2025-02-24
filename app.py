import time
import os
import uuid
from datetime import timedelta
from flask import Flask, request, jsonify, session
from flask_session import Session
import redis
import openai
from flask_cors import CORS

# --- Firebase Bağlantısı için Eklemeler Başlangıç ---
import firebase_admin
from firebase_admin import credentials, db

# Ortam değişkenlerinden gerekli bilgileri alıyoruz:
service_account_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
firebase_db_url = os.environ.get('FIREBASE_DB_URL')

if not service_account_path or not firebase_db_url:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS veya FIREBASE_DB_URL ortam değişkeni ayarlanmamış!")

# Firebase Admin SDK'yı, hizmet hesabı dosyası ve veritabanı URL’i ile başlatıyoruz.
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': firebase_db_url
})
# --- Firebase Bağlantısı için Eklemeler Bitiş ---

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
CORS(app, supports_credentials=True)  # Tüm originlerden gelen istekleri kabul eder

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=2)

# Ortam değişkeninden OpenAI API anahtarını alıyoruz.
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY ortam değişkeni ayarlanmamış!")

# Redis URL'si: "redis://" ile başlamalıdır.
redis_url = os.getenv("REDIS_URL")

# Flask-Session için konfigürasyon
app.config["SESSION_COOKIE_NAME"] = "my_custom_session"
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REDIS"] = redis.from_url(redis_url)
# Flask-Session'ı başlat
Session(app)

# Sistem promptunu tanımlayın (uzun prompt metniniz buraya gelecek)
system_prompt = """
en, Growkent'in akıllı müşteri destek asistanısın. Growkent, hobi bahçecilik ürünleri satmaktadır. Görevin, müşterilere doğru, net ve profesyonel yanıtlar vermek, onlara en iyi alışveriş deneyimini sunmaktır.
...
"""

@app.route("/chat", methods=["POST"])
def chat():
    session.permanent = True
    data = request.get_json()
    user_message = data.get("message")
    if not user_message:
        return jsonify({"error": "Mesaj bulunamadı"}), 400

    # Eğer session'da "conversation_history" yoksa, initialize et.
    if "conversation_history" not in session:
        session["conversation_history"] = []

    conversation_history = session["conversation_history"]
    conversation_history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": system_prompt}] + conversation_history

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-2024-11-20",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        bot_message = response.choices[0].message.get("content", "").strip()
        conversation_history.append({"role": "assistant", "content": bot_message})
        session["conversation_history"] = conversation_history  # Session güncellemesi

        # Kullanıcıya özel conversation_id oluşturma (eğer yoksa)
        if "conversation_id" not in session:
            session["conversation_id"] = str(uuid.uuid4())
        conversation_id = session["conversation_id"]

        # Firebase'de tek bir conversation altında verileri güncelleme
        ref = db.reference('conversations').child(conversation_id)
        ref.set({
            'conversation': conversation_history,
            'timestamp': int(time.time())
        })

        return jsonify({"message": bot_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
