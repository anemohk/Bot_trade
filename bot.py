# bot.py - سكريبت كامل معدل
import os
from flask import Flask, request
import telegram
import requests
from io import BytesIO

# تهيئة التطبيق
app = Flask(__name__)

# تحميل المتغيرات البيئية
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# تهيئة بوت Telegram
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def analyze_chart(image_path):
    """تحليل الصورة باستخدام DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        with open(image_path, 'rb') as img_file:
            response = requests.post(
                "https://api.deepseek.com/v1/vision/analyze",  # تأكد من الرابط حسب الوثائق
                headers=headers,
                files={"image": img_file},
                data={"prompt": "حلل منحنى التداول وأعط إشارة (شراء/بيع/انتظر) مع السبب"}
            )
        return response.json().get("analysis", "لا يمكن تحليل الصورة")
    except Exception as e:
        return f"خطأ في التحليل: {str(e)}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        chat_id = update.message.chat.id

        if update.message.photo:
            # معالجة الصورة
            file_id = update.message.photo[-1].file_id
            photo = bot.get_file(file_id)
            img_path = "temp_chart.jpg"
            photo.download(img_path)
            
            # تحليل الصورة
            analysis = analyze_chart(img_path)
            bot.send_message(
                chat_id=chat_id,
                text=f"📊 نتيجة التحليل:\n{analysis}\n\n⚠️ ملاحظة: هذه ليست نصيحة مالية"
            )
            
            # حذف الصورة المؤقتة
            if os.path.exists(img_path):
                os.remove(img_path)
        else:
            bot.send_message(
                chat_id=chat_id,
                text="📤 يرجى إرسال صورة منحنى تداول فقط\nمثال:"
            )
            bot.send_photo(
                chat_id=chat_id,
                photo=open("example_chart.jpg", 'rb')  # أضف ملف مثال اختياري
            )
    except Exception as e:
        bot.send_message(
            chat_id=chat_id,
            text=f"❌ حدث خطأ: {str(e)}"
        )
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
