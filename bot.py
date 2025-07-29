import os
import sys
from flask import Flask, request, jsonify
import telegram

# تجنب تحميل pkg_resources
os.environ["SETUPTOOLS_USE_DISTUTILS"] = "stdlib"

app = Flask(__name__)

# التحقق من وجود التوكن
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    print("❌ خطأ: لم يتم تعيين TELEGRAM_TOKEN")
    sys.exit(1)

# تهيئة البوت مع معالجة الأخطاء
try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    print(f"✅ تم تهيئة البوت باستخدام التوكن: {TELEGRAM_TOKEN[:10]}...")
except Exception as e:
    print(f"❌ فشل تهيئة البوت: {str(e)}")
    sys.exit(1)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        chat_id = update.message.chat.id
        
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            bot.send_message(chat_id, f"📸 تم استلام صورة (ID: {file_id})")
        else:
            bot.send_message(chat_id, "مرحباً! أرسل صورة منحنى تداول لتحليلها")
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "🤖 خادم بوت التداول يعمل بنجاح!"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 بدء التشغيل على المنفذ {port}")
    app.run(host='0.0.0.0', port=port)
