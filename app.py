import time
import os
import uuid
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import firebase_admin
from firebase_admin import credentials, db

# Firebase bağlantısı
if not firebase_admin._apps:
    firebase_credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    cred = credentials.Certificate(json.loads(firebase_credentials_json))
    firebase_admin.initialize_app(cred, {'databaseURL': os.getenv("FIREBASE_DB_URL")})

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

CORS(app,
     origins=["https://www.growkent.com"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
)

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY ortam değişkeni ayarlanmamış!")

assistant_id = os.getenv("OPENAI_ASSISTANT_ID")  # Assistant API'den aldığın Assistant ID
if not assistant_id:
    raise ValueError("OPENAI_ASSISTANT_ID ortam değişkeni ayarlanmamış!")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")
    conversation_id = data.get("conversation_id")

    if not user_message:
        return jsonify({"error": "Mesaj bulunamadı"}), 400

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        thread = openai.beta.threads.create()
        thread_id = thread.id
    else:
        ref = db.reference('conversations').child(conversation_id)
        stored_data = ref.get()
        thread_id = stored_data.get('thread_id') if stored_data else openai.beta.threads.create().id

    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Assistant yanıt verene kadar bekle
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == 'completed':
            break
        time.sleep(1)

    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    bot_message = messages.data[0].content[0].text.value

    # Firebase'e konuşmayı kaydet
    ref = db.reference('conversations').child(conversation_id)
    ref.set({
        'thread_id': thread_id,
        'timestamp': int(time.time())
    })

    return jsonify({
        "message": bot_message,
        "conversation_id": conversation_id
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
