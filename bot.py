import os
from flask import Flask, request
import telegram
import requests
from io import BytesIO

app = Flask(__name__)

# تحميل المفاتيح من متغيرات البيئة (آمن)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def analyze_with_deepseek(image_path):
    """إرسال الصورة إلى DeepSeek API للتحليل"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # إذا كان DeepSeek يدعم الصور (تحقق من وثائق API)
    with open(image_path, 'rb') as img_file:
        response = requests.post(
            "https://api.deepseek.com/v1/vision",  # تغيير الرابط حسب الوثائق الرسمية
            headers=headers,
            files={"image": img_file},
            data={"prompt": "حلل منحنى Quotex وأعطي إشارة تداول (شراء/بيع/انتظر)"}
        )
    
    return response.json().get("choices", [{}])[0].get("message", "لا يمكن تحليل الصورة")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id

    if update.message.photo:
        # تنزيل الصورة
        file_id = update.message.photo[-1].file_id
        photo = bot.get_file(file_id)
        img_path = "temp_chart.jpg"
        photo.download(img_path)
        
        # التحليل
        try:
            analysis = analyze_with_deepseek(img_path)
            bot.send_message(chat_id=chat_id, text=f"📊 النتيجة: {analysis}")
        except Exception as e:
            bot.send_message(chat_id=chat_id, text="❌ حدث خطأ في التحليل")
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)  # حذف الصورة المؤقتة
    else:
        bot.send_message(chat_id=chat_id, text="📤 أرسل صورة منحنى Quotex فقط")

    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
