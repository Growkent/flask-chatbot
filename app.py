
import os
import time
import uuid
import json
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, db

# Logging
logging.basicConfig(level=logging.INFO)

# OpenAI ayarları
api_key = os.getenv("OPENAI_API_KEY")
prompt_id = os.getenv("OPENAI_PROMPT_ID")
prompt_version = os.getenv("OPENAI_PROMPT_VERSION", "4")

if not api_key:
    raise ValueError("OPENAI_API_KEY ortam değişkeni eksik!")

if not prompt_id:
    raise ValueError("OPENAI_PROMPT_ID ortam değişkeni eksik!")

client = OpenAI(
    api_key=api_key,
    timeout=60.0,
    max_retries=2
)

# Firebase bağlantısı
if not firebase_admin._apps:
    firebase_credentials_json = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS_JSON"
    )
    firebase_db_url = os.getenv("FIREBASE_DB_URL")

    if not firebase_credentials_json:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS_JSON ortam değişkeni eksik!"
        )

    if not firebase_db_url:
        raise ValueError("FIREBASE_DB_URL ortam değişkeni eksik!")

    cred = credentials.Certificate(
        json.loads(firebase_credentials_json)
    )

    firebase_admin.initialize_app(
        cred,
        {"databaseURL": firebase_db_url}
    )

    logging.info("Firebase başarıyla başlatıldı.")

# Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

CORS(
    app,
    origins=["https://www.growkent.com"],
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ]
)


def get_ai_response(user_message, previous_response_id=None):
    """Prompt sürümünü kullanarak Responses API'den yanıt alır."""

    params = {
        "prompt": {
            "id": prompt_id,
            "version": prompt_version
        },
        "input": user_message
    }

    # Varsa önceki yanıt üzerinden konuşmayı sürdür.
    if previous_response_id:
        params["previous_response_id"] = previous_response_id

    response = client.responses.create(**params)

    bot_message = response.output_text

    if not bot_message:
        raise ValueError("OpenAI boş bir yanıt döndürdü.")

    return bot_message, response.id


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}

        user_message = data.get("message")
        conversation_id = data.get("conversation_id")

        if not isinstance(user_message, str) or not user_message.strip():
            return jsonify({"error": "Mesaj bulunamadı."}), 400

        # İlk mesajda yeni bir konuşma kimliği oluştur.
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        ref = db.reference("conversations").child(conversation_id)
        stored_data = ref.get() or {}

        previous_response_id = stored_data.get("previous_response_id")

        logging.info(
            "Chat mesajı alındı. conversation_id=%s",
            conversation_id
        )

        bot_message, response_id = get_ai_response(
            user_message.strip(),
            previous_response_id
        )

        # Son yanıt kimliğini sakla.
        ref.set({
            "previous_response_id": response_id,
            "timestamp": int(time.time())
        })

        return jsonify({
            "message": bot_message,
            "conversation_id": conversation_id
        })

    except Exception:
        logging.exception("Chat sırasında hata oluştu.")
        return jsonify({
            "error": "Yanıt oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
        }), 500


@app.route("/manychat", methods=["POST"])
def manychat():
    try:
        data = request.get_json(silent=True) or {}

        user_message = data.get("message")
        user_id = data.get("user_id")

        if (
            not isinstance(user_message, str)
            or not user_message.strip()
            or not user_id
        ):
            return jsonify({
                "response": "Mesaj veya kullanıcı bilgisi eksik."
            }), 400

        user_id = str(user_id)

        ref = db.reference("manychat_conversations").child(user_id)
        stored_data = ref.get() or {}

        previous_response_id = stored_data.get("previous_response_id")

        logging.info(
            "ManyChat mesajı alındı. user_id=%s",
            user_id
        )

        bot_message, response_id = get_ai_response(
            user_message.strip(),
            previous_response_id
        )

        ref.set({
            "previous_response_id": response_id,
            "timestamp": int(time.time())
        })

        return jsonify({
            "response": bot_message,
            "thread_id": response_id,
            "response_id": response_id
        })

    except Exception:
        logging.exception("ManyChat sırasında hata oluştu.")
        return jsonify({
            "response": "Yanıt oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
        }), 500
