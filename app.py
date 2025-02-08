from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

@app.route("/")
def home():
    return "Flask uygulaman çalışıyor!"

# OpenAI API Anahtarını Tanımla (LÜTFEN GİZLİ TUT)
openai.api_key = "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"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    if not user_message:
        return jsonify({"reply": "Lütfen bir mesaj girin."}), 400

    # Yasaklı konular
    forbidden_topics = ["marihuana", "cannabis", "kenevir", "tohumu", "yetiştiricilik"]
    if any(topic in user_message for topic in forbidden_topics):
        return jsonify({"reply": "Üzgünüm, bu konu hakkında yardımcı olamıyorum."})

    # Özel yanıtlar
    if "sipariş takibi" in user_message or "kargom nerede" in user_message:
        return jsonify({"reply": "Sipariş numaranızı paylaşın, kargo durumunuzu kontrol edelim."})
    
    elif "iade nasıl yapılır" in user_message or "ürünü iade etmek istiyorum" in user_message:
        return jsonify({"reply": "Ürünü 14 gün içinde orijinal ambalajında iade edebilirsiniz. Detaylı bilgi: [İade Politikası Linki]"})
    
    elif "kampanyalar" in user_message or "indirim var mı" in user_message:
        return jsonify({"reply": "Şu an devam eden kampanyalarımız: Outlet ürünlerde %50'ye varan indirimler, Kasa önü fırsat ürünlerinde %10 indirim, Haftanın fırsat ürününde %15 indirim! Daha fazla bilgi için web sitemizi ziyaret edebilirsiniz: https://www.growkent.com"})
    
    elif "hangi gübreyi kullanmalıyım" in user_message:
        return jsonify({"reply": "Bitkileriniz için en uygun gübre seçimi için hangi bitkiyi yetiştirdiğinizi belirtir misiniz? Önerdiğimiz gübreler hakkında detaylı bilgi için: [Ürün Linki]"})
    
    elif "iş başvurusu" in user_message:
        return jsonify({"reply": "İş başvurusu yapmak için destek@growkent.com mail adresine CV'nizi gönderebilirsiniz."})

    # Genel OpenAI Yanıtı
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Sen, Growkent'in akıllı müşteri destek asistanısın. Müşterilere doğru, net ve profesyonel yanıtlar veriyorsun. Growkent, hobi bahçecilik ürünleri satmaktadır. Müşterilere sipariş, kargo, iade, ürün kullanımı ve kampanyalar hakkında yardımcı oluyorsun."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"Bir hata oluştu: {str(e)}"

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
