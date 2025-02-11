import os
from openai import OpenAI
from flask import Flask, request, jsonify

app = Flask(__name__)

# OpenAI API Anahtarını Çevresel Değişkenden Al
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route("/", methods=["GET"])
def home():
    return "Chatbot API Çalışıyor! Lütfen /chat endpoint’ini POST methodu ile kullanın."

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    customer_id = request.json.get("customer_id", "anonim")
    
    if not user_message:
        return jsonify({"error": "Mesaj içeriği boş olamaz"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [{"type": "text", "text": user_message}]}
            ],
            response_format={"type": "text"},
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "customer_support",
                        "strict": True,
                        "parameters": {
                            "type": "object",
                            "required": [
                                "customer_query",
                                "customer_id",
                                "category",
                                "follow_up_needed",
                                "timestamp"
                            ],
                            "properties": {
                                "category": {"type": "string", "description": "Belirli bir ürün veya hizmet kategorisi"},
                                "timestamp": {"type": "string", "description": "Soru veya talebin alındığı zaman damgası"},
                                "customer_id": {"type": "string", "description": "Müşterinin tanımlayıcı kimliği"},
                                "customer_query": {"type": "string", "description": "Müşterinin sorduğu soru veya talep"},
                                "follow_up_needed": {"type": "boolean", "description": "Ek bilgiye ihtiyaç duyulup duyulmadığı"}
                            },
                            "additionalProperties": False
                        },
                        "description": "Growkent'in akıllı müşteri destek asistanıdır."
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "customer_support"}},
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
