import os
import sys
import asyncio
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.error import InvalidToken

# إنشاء تطبيق Flask
app = Flask(__name__)

# التوكن الثابت
TELEGRAM_TOKEN = "8059201152:AAH8uTx33ZeZFENmWrFBtFX7uGQJtvQcNbw"

# إنشاء كائن Bot بشكل غير متزامن
bot = Bot(token=TELEGRAM_TOKEN)

# تهيئة البوت بشكل غير متزامن
async def initialize_bot():
    try:
        bot_info = await bot.get_me()
        print(f"✅ تم تهيئة البوت بنجاح: @{bot_info.username}")
        return True
    except InvalidToken as e:
        print(f"❌ توكن غير صالح: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع أثناء تهيئة البوت: {e}")
        return False

# تشغيل التهيئة عند بدء التطبيق
if not asyncio.run(initialize_bot()):
    sys.exit(1)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # تحويل بيانات الطلب إلى كائن Update
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot)
        
        # التحقق من وجود الرسالة
        if not update or not update.message:
            return jsonify({"status": "error", "message": "تنسيق تحديث غير صالح"}), 400
        
        chat_id = update.message.chat.id

        # إرسال رسالة تأكيد
        asyncio.run(bot.send_message(
            chat_id=chat_id,
            text="📩 تم استلام رسالتك بنجاح!"
        ))
        
        # معالجة الصور
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            asyncio.run(bot.send_message(
                chat_id=chat_id,
                text=f"📸 تم استلام صورة (ID: {file_id})\n\nجاري التحليل..."
            ))
            
            # نتيجة تحليل وهمية
            asyncio.run(bot.send_message(
                chat_id=chat_id,
                text="📊 نتيجة التحليل الافتراضي:\n"
                     "• النمط: صاعد\n• التوصية: شراء\n"
                     "🎯 هدف الربح: 5%\n🛑 وقف الخسارة: 3%"
            ))
            
        # معالجة الرسائل النصية
        elif update.message.text:
            message_text = update.message.text
            
            if message_text == '/start':
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text="✅ البوت يعمل بنجاح!\n📈 أرسل صورة منحنى تداول لتحليلها"
                ))
            elif message_text == '/help':
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text="❓ كيفية الاستخدام:\n"
                         "1. أرسل صورة منحنى تداول\n"
                         "2. انتظر التحليل\n"
                         "3. احصل على التوصية\n\n"
                         "الأوامر المتاحة:\n"
                         "/start - بدء المحادثة\n"
                         "/help - المساعدة"
                ))
            else:
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text="❌ لم أفهم طلبك. أرسل /help لرؤية التعليمات."
                ))
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        print(f"❌ خطأ في معالجة الويب هوك: {e}")
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
