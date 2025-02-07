from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

@app.route("/")
def home():
    return "Flask uygulaman çalışıyor!"

# OpenAI API Anahtarını Tanımla
openai.api_key = "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"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message").lower()

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
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sen, Growkent'in akıllı müşteri destek asistanısın. Müşterilere doğru, net ve profesyonel yanıtlar veriyorsun. Growkent, hobi bahçecilik ürünleri satmaktadır. Müşterilere sipariş, kargo, iade, ürün kullanımı ve kampanyalar hakkında yardımcı oluyorsun."},
            {"role": "user", "content": user_message}
        ]
    )

    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
