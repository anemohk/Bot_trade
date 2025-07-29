# bot.py - النسخة النهائية
import os
import sys
from flask import Flask, request, jsonify
import telegram

# تهيئة التطبيق
app = Flask(__name__)

# التحقق من وجود التوكن قبل التهيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    print("❌ خطأ: لم يتم تعيين TELEGRAM_TOKEN في متغيرات البيئة")
    sys.exit(1)

# تهيئة بوت Telegram
try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    bot_info = bot.get_me()
    print(f"✅ تم تهيئة البوت بنجاح: @{bot_info.username}")
except telegram.error.InvalidToken:
    print("❌ توكن غير صالح! تأكد من صحة TELEGRAM_TOKEN")
    sys.exit(1)
except Exception as e:
    print(f"❌ خطأ غير متوقع: {str(e)}")
    sys.exit(1)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # تحويل البيانات إلى كائن Update
        update_data = request.get_json(force=True)
        update = telegram.Update.de_json(update_data, bot)
        
        # التحقق من وجود الرسالة والمحتوى
        if not update or not update.message:
            return jsonify({"status": "error", "message": "Invalid update format"}), 400
        
        chat_id = update.message.chat.id
        message_text = update.message.text or ""
        
        if update.message.photo:
            # معالجة الصور
            file_id = update.message.photo[-1].file_id
            bot.send_message(
                chat_id,
                f"📸 تم استلام صورة (ID: {file_id})\n\n🔍 جاري التحليل..."
            )
        elif message_text:
            # معالجة الرسائل النصية
            if message_text.startswith('/'):
                if message_text == '/start':
                    response = "مرحبًا! أنا بوت تحليل منحنيات التداول 📈\nأرسل لي صورة منحنى Quotex وسأحللها لك"
                elif message_text == '/help':
                    response = "❓ المساعدة:\n- أرسل صورة منحنى تداول لتحليلها\n- /token للتحقق من حالة التوكن"
                elif message_text == '/token':
                    token_status = "✅ التوكن صالح ويعمل" if TELEGRAM_TOKEN else "❌ التوكن غير معين"
                    response = f"حالة التوكن:\n{token_status}"
                else:
                    response = "⚠️ الأمر غير معروف"
            else:
                response = "📤 يرجى إرسال صورة منحنى تداول أو استخدام الأوامر المتاحة"
            
            bot.send_message(chat_id, response)
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        error_msg = f"❌ خطأ في معالجة الويب هوك: {str(e)}"
        print(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/health')
def health_check():
    """نقطة نهاية للتحقق من صحة الخدمة"""
    token_status = "✅ موجود" if TELEGRAM_TOKEN else "❌ مفقود"
    return jsonify({
        "status": "running",
        "token_status": token_status,
        "bot_ready": "✅" if TELEGRAM_TOKEN and 'bot' in globals() else "❌"
    })

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return "🤖 خادم بوت التداول يعمل! استخدم /webhook لاستقبال تحديثات Telegram"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 بدء التشغيل على المنفذ {port}...")
    app.run(host='0.0.0.0', port=port)
