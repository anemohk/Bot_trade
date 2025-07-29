import os
import sys
from flask import Flask, request, jsonify
import telegram

# تجنب مشاكل حزم setuptools
os.environ["SETUPTOOLS_USE_DISTUTILS"] = "stdlib"

# إنشاء تطبيق Flask
app = Flask(__name__)

# التوكن الثابت (سيتم تغييره بعد الاختبار)
TELEGRAM_TOKEN = "8059201152:AAH8uTx33ZeZFENmWrFBtFX7uGQJtvQcNbw"

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
            
            # إرسال نتيجة وهمية للاختبار
            bot.send_message(
                chat_id,
                "📊 نتيجة التحليل الافتراضي:\n"
                "• النمط: صاعد\n• القوة: متوسطة\n• التوصية: شراء\n"
                "🎯 هدف الربح: 5%\n🛑 وقف الخسارة: 3%\n\n"
                "⚠️ هذه نتيجة تجريبية فقط"
            )
            
        # إذا كانت رسالة نصية
        elif update.message.text:
            message_text = update.message.text
            
            # معالجة الأوامر
            if message_text == '/start':
                bot.send_message(
                    chat_id,
                    "✅ البوت يعمل بنجاح!\n"
                    "📈 أرسل صورة منحنى تداول لتحليلها"
                )
            elif message_text == '/token':
                bot.send_message(
                    chat_id,
                    f"🔑 التوكن المستخدم:\n{TELEGRAM_TOKEN}\n\n"
                    "⚠️ سيتم تغييره بعد الاختبار"
                )
            elif message_text == '/delete':
                bot.send_message(
                    chat_id,
                    "🛑 تم حذف التوكن من الذاكرة المؤقتة\n"
                    "يرجى تغيير التوكن في السكريبت"
                )
                # هذا مثال فقط، التوكن سيظل في السكريبت
            else:
                bot.send_message(
                    chat_id,
                    "❌ لم أفهم طلبك. الأوامر المتاحة:\n"
                    "/start - بدء البوت\n"
                    "/token - عرض التوكن المستخدم\n"
                    "/delete - حذف التوكن (رمزى)"
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
        "telegram_bot": "active",
        "python_version": sys.version.split()[0]
    })

if __name__ == '__main__':
    port = 5000
    print(f"🚀 بدء التشغيل على المنفذ {port}")
    print(f"🔑 التوكن المستخدم: {TELEGRAM_TOKEN}")
    app.run(host='0.0.0.0', port=port)
