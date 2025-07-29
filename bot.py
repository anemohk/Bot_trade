import os
import sys
from flask import Flask, request, jsonify
import telegram

# تجنب مشاكل حزم setuptools
os.environ["SETUPTOOLS_USE_DISTUTILS"] = "stdlib"

# إنشاء تطبيق Flask
app = Flask(__name__)

# الحصول على توكن البوت من متغير البيئة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    print("❌ خطأ: لم يتم تعيين TELEGRAM_TOKEN في متغيرات البيئة.")
    sys.exit(1)

# تهيئة بوت Telegram
try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    bot_info = bot.get_me()
    print(f"✅ تم تهيئة البوت بنجاح: @{bot_info.username}")
except telegram.error.InvalidToken as e:
    print(f"❌ توكن غير صالح: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ خطأ غير متوقع أثناء تهيئة البوت: {e}")
    sys.exit(1)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # تحويل بيانات الطلب إلى كائن Update
        update_data = request.get_json(force=True)
        update = telegram.Update.de_json(update_data, bot)
        
        # التحقق من وجود الرسالة
        if not update or not update.message:
            return jsonify({"status": "error", "message": "تنسيق تحديث غير صالح"}), 400
        
        chat_id = update.message.chat.id

        # إذا كانت الرسالة تحتوي على صورة
        if update.message.photo:
            # نأخذ أعلى دقة صورة (آخر عنصر في القائمة)
            file_id = update.message.photo[-1].file_id
            
            # إرسال رسالة تأكيد
            bot.send_message(
                chat_id, 
                f"📸 تم استلام صورة (ID: {file_id})\n\nجاري التحليل..."
            )
            
            # هنا يمكنك إضافة تحليل الصورة
            # analysis = analyze_image(file_id)
            # bot.send_message(chat_id, analysis)
            
        # إذا كانت رسالة نصية
        elif update.message.text:
            message_text = update.message.text
            
            # معالجة الأوامر
            if message_text == '/start':
                bot.send_message(
                    chat_id,
                    "مرحبًا! 👋 أنا بوت تحليل منحنيات التداول.\n"
                    "أرسل لي صورة منحنى Quotex وسأحاول تحليلها لك."
                )
            elif message_text == '/help':
                bot.send_message(
                    chat_id,
                    "❓ كيفية الاستخدام:\n"
                    "1. أرسل صورة منحنى تداول من Quotex\n"
                    "2. انتظر التحليل\n"
                    "3. احصل على التوصية\n\n"
                    "الأوامر المتاحة:\n"
                    "/start - بدء المحادثة\n"
                    "/help - المساعدة\n"
                    "/status - حالة الخادم"
                )
            elif message_text == '/status':
                bot.send_message(
                    chat_id,
                    "🟢 الخادم يعمل بشكل طبيعي\n"
                    f"الإصدار: 1.0\n"
                    f"معرف البوت: @{bot_info.username}"
                )
            else:
                bot.send_message(
                    chat_id,
                    "❌ لم أفهم طلبك. أرسل /help لرؤية التعليمات."
                )
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        # طباعة الخطأ في السجلات
        print(f"❌ خطأ في معالجة الويب هوك: {e}")
        # إرسال رسالة خطأ للمستخدم
        bot.send_message(chat_id, "حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقًا.")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "🤖 خادم بوت تحليل التداول يعمل بنجاح!"

@app.route('/health')
def health_check():
    return jsonify({
        "status": "running",
        "telegram_bot": "active" if TELEGRAM_TOKEN else "inactive",
        "python_version": sys.version.split()[0]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 بدء التشغيل على المنفذ {port}")
    app.run(host='0.0.0.0', port=port)
