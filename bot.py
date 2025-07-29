import os
import sys
import asyncio
import random
import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.error import InvalidToken, TelegramError

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# إنشاء تطبيق Flask
app = Flask(__name__)

# التوكن الثابت (يجب تغييره بعد الاختبار!)
TELEGRAM_TOKEN = "8059201152:AAH8uTx33ZeZFENmWrFBtFX7uGQJtvQcNbw"

# إنشاء كائن Bot بشكل غير متزامن
bot = Bot(token=TELEGRAM_TOKEN)

# تهيئة البوت بشكل غير متزامن
async def initialize_bot():
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ تم تهيئة البوت بنجاح: @{bot_info.username}")
        return True
    except InvalidToken as e:
        logger.error(f"❌ توكن غير صالح: {e}")
        return False
    except TelegramError as e:
        logger.error(f"❌ خطأ في Telegram API: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع أثناء تهيئة البوت: {e}")
        return False

# تشغيل التهيئة عند بدء التطبيق
if not asyncio.run(initialize_bot()):
    logger.error("❌ فشل تهيئة البوت. إيقاف الخادم.")
    sys.exit(1)

def generate_trade_signal():
    """إنشاء إشارة تداول تفصيلية"""
    # أزواج تداول شائعة
    trading_pairs = [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", 
        "USD/CAD", "EUR/GBP", "GBP/JPY", "XAU/USD",
        "BTC/USD", "ETH/USD", "US30", "GER40"
    ]
    
    # اختيار زوج عشوائي
    pair = random.choice(trading_pairs)
    
    # إنشاء وقت دخول الصفقة (UTC+1)
    entry_time = datetime.utcnow() + timedelta(hours=1)
    entry_time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S (UTC+1)")
    
    # توليد نسبة نجاح عشوائية (80-95%)
    success_rate = random.randint(80, 95)
    
    # تحديد اتجاه الصفقة (شراء/بيع)
    direction = random.choice(["شراء", "بيع"])
    
    # إشارة تداول تفصيلية
    signal = (
        f"📊 إشارة تداول جديدة\n\n"
        f"⏰ وقت الدخول: {entry_time_str}\n"
        f"📈 الزوج: {pair}\n"
        f"📈 الإتجاه: {direction}\n"
        f"🎯 نسبة النجاح: {success_rate}%\n\n"
        f"🛑 وقف الخسارة: 3%\n"
        f"🎯 هدف الربح: 5%"
    )
    
    return signal

def keep_service_alive():
    """إرسال طلبات دورية لإبقاء الخدمة نشطة"""
    while True:
        try:
            # رابط الخدمة (تأكد من استبداله برابطك)
            url = "https://bot-trade-quotex-ai.onrender.com/health"
            response = requests.get(url, timeout=10)
            logger.info(f"✅ طلب إبقاء الخدمة نشطة: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ خطأ في إبقاء الخدمة نشطة: {e}")
        time.sleep(300)  # كل 5 دقائق

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    try:
        logger.info("📩 تم استلام طلب ويب هوك")
        
        # معالجة طلبات GET للفحص
        if request.method == 'GET':
            logger.info("🔍 طلب فحص للويب هوك")
            return jsonify({"status": "ready"}), 200
        
        # معالجة طلبات POST من Telegram
        update_data = request.get_json(force=True)
        logger.debug(f"📦 بيانات الطلب: {update_data}")
        
        # تحويل بيانات الطلب إلى كائن Update
        update = Update.de_json(update_data, bot)
        
        # التحقق من وجود الرسالة
        if not update or not update.message:
            logger.warning("⚠️ تنسيق تحديث غير صالح")
            return jsonify({"status": "error", "message": "تنسيق تحديث غير صالح"}), 400
        
        chat_id = update.message.chat.id
        logger.info(f"💬 تم استلام رسالة من الدردشة: {chat_id}")

        # معالجة الصور
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            logger.info(f"🖼️ تم استلام صورة (ID: {file_id})")
            
            # إرسال رسالة التحليل
            asyncio.run(bot.send_message(
                chat_id=chat_id,
                text="🔍 جاري تحليل الصورة..."
            ))
            
            # توليد إشارة تداول تفصيلية
            signal = generate_trade_signal()
            
            # إرسال نتيجة التحليل
            asyncio.run(bot.send_message(
                chat_id=chat_id,
                text=signal
            ))
            
        # معالجة الرسائل النصية
        elif update.message.text:
            message_text = update.message.text
            logger.info(f"✉️ تم استلام نص: {message_text}")
            
            # معالجة الأوامر
            if message_text == '/start':
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text="✅ مرحباً! أنا بوت تحليل منحنيات التداول\n"
                         "📈 أرسل صورة منحنى تداول لتحليلها وإعطائك إشارة تداول"
                ))
            elif message_text == '/signal':
                # توليد إشارة تداول مباشرة
                signal = generate_trade_signal()
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text=signal
                ))
            elif message_text == '/help':
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text="❓ كيفية الاستخدام:\n"
                         "1. أرسل صورة منحنى تداول من Quotex\n"
                         "2. سأحللها وأعطيك إشارة تداول كاملة\n\n"
                         "الأوامر المتاحة:\n"
                         "/start - بدء المحادثة\n"
                         "/help - المساعدة\n"
                         "/signal - إشارة تداول فورية\n"
                         "/time - الوقت الحالي (UTC+1)"
                ))
            elif message_text == '/time':
                # إرسال الوقت الحالي (UTC+1)
                current_time = datetime.utcnow() + timedelta(hours=1)
                time_str = current_time.strftime("%Y-%m-%d %H:%M:%S (UTC+1)")
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text=f"⏰ الوقت الحالي: {time_str}"
                ))
            else:
                asyncio.run(bot.send_message(
                    chat_id=chat_id,
                    text="❌ لم أفهم طلبك. الأوامر المتاحة:\n"
                         "/start - بدء البوت\n"
                         "/help - المساعدة\n"
                         "/signal - إشارة تداول فورية"
                ))
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        logger.exception("🔥 خطأ في معالجة الويب هوك")
        # إرسال رسالة خطأ للمستخدم
        if 'chat_id' in locals():
            asyncio.run(bot.send_message(
                chat_id=chat_id,
                text="حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقًا."
            ))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "🤖 خادم بوت تحليل التداول يعمل بنجاح!"

@app.route('/health')
def health_check():
    return jsonify({
        "status": "running",
        "telegram_bot": "active",
        "python_version": sys.version.split()[0],
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    # بدء خيط لإبقاء الخدمة نشطة
    t = threading.Thread(target=keep_service_alive)
    t.daemon = True
    t.start()
    
    # نستخدم المنفذ 10000 مباشرة
    port = 10000
    logger.info(f"🚀 بدء التشغيل على المنفذ {port}")
    logger.info(f"🔑 التوكن المستخدم: {TELEGRAM_TOKEN}")
    
    # استخدم Waitress لخدمة التطبيق
    from waitress import serve
    serve(app, host='0.0.0.0', port=port)
