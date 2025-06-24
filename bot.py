# =============================================================================
#           Final Corrected Code for bot.py - © 2024 Gemini AI
# =============================================================================

import os
import telegram
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import yfinance as yf

# --- استدعاء المتغيرات الآمنة من بيئة الاستضافة (Render) ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

# --- إعداد البوت والخادم ---
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)
scheduler = BackgroundScheduler(timezone="UTC")

# --- إعداد قاعدة البيانات (ذاكرة البوت) ---
def init_db():
    """
    تنشئ هذه الدالة جدول الصفقات في قاعدة البيانات إذا لم يكن موجودًا.
    """
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            expiry_minutes INTEGER NOT NULL,
            entry_time TIMESTAMP NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- الوظائف المساعدة ---
async def send_telegram_message(message):
    """
    دالة لإرسال الرسائل إلى قناة التليجرام.
    """
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def get_current_price(symbol):
    """
    تجلب السعر الحالي للزوج من Yahoo Finance.
    """
    try:
        # تحويل الصيغة لتناسب Yahoo Finance (مثال: EURUSD -> EURUSD=X)
        ticker = yf.Ticker(f"{symbol}=X")
        data = ticker.history(period='1d', interval='1m')
        if not data.empty:
            return data['Close'].iloc[-1]
        print(f"No current price data found for {symbol}")
        return None
    except Exception as e:
        print(f"Could not fetch price for {symbol} from yfinance: {e}")
        return None

def check_trade_outcome(trade_id):
    """
    تتحقق من نتيجة الصفقة بعد انتهاء مدتها وترسل النتيجة.
    """
    with app.app_context():
        conn = sqlite3.connect('trades.db')
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, direction, entry_price FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            print(f"Trade ID {trade_id} not found in database.")
            conn.close()
            return

        symbol, direction, entry_price = trade
        current_price = get_current_price(symbol)

        if current_price is None:
            print(f"Could not determine outcome for trade {trade_id}, no current price available.")
            conn.close()
            return

        # تحديد الفوز أو الخسارة
        if direction == "CALL":
            result = "WIN" if current_price > entry_price else "LOSS"
        elif direction == "PUT":
            result = "WIN" if current_price < entry_price else "LOSS"
        else:
            result = "UNKNOWN"

        cursor.execute("UPDATE trades SET status = ? WHERE id = ?", (result, trade_id))
        conn.commit()
        
        outcome_symbol = "✅" if result == "WIN" else "❌"
        # رسالة النتيجة المفصلة
        outcome_message = f"""
*{outcome_symbol} نـتـيـجـة الـصـفـقـة {outcome_symbol}*

▫️ *الزوج:* {symbol}
▫️ *الاتجاه:* {direction}
▫️ *النتيجة:* *{result}*
▫️ *سعر الدخول:* `{entry_price:.5f}`
▫️ *السعر عند الإغلاق:* `{current_price:.5f}`
"""
        asyncio.run(send_telegram_message(outcome_message))
        conn.close()

# --- نقطة استقبال الإشارات من TradingView ---
@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    تستقبل الإشارة كـ Webhook من TradingView.
    """
    try:
        data = json.loads(request.get_data(as_text=True))
        symbol = data['symbol']
        direction = data['direction']
        entry_price = data['entry_price']
        expiry_minutes = data['expiry_minutes']
        
        # 1. إرسال رسالة الإشارة الجديدة (بدون سعر الدخول)
        new_trade_message = f"""
🔔 *إشـارة جـديـدة* 🔔

▫️ *الزوج:* {symbol}
▫️ *الاتجاه:* {direction}
▫️ *مدة الصفقة:* {expiry_minutes} دقائق
"""
        asyncio.run(send_telegram_message(new_trade_message))

        # 2. تسجيل الصفقة في قاعدة البيانات
        conn = sqlite3.connect('trades.db')
        cursor = conn.cursor()
        entry_time = datetime.utcnow()
        cursor.execute(
            "INSERT INTO trades (symbol, direction, entry_price, expiry_minutes, entry_time, status) VALUES (?, ?, ?, ?, ?, ?)",
            (symbol, direction, entry_price, expiry_minutes, entry_time, "PENDING")
        )
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 3. جدولة التحقق من النتيجة
        run_time = datetime.now() + timedelta(minutes=expiry_minutes)
        scheduler.add_job(check_trade_outcome, 'date', run_date=run_time, args=[trade_id])
        
        return "Alert Received and Scheduled", 200

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return "Error while processing webhook", 400

# --- نقطة النهاية الرئيسية للتأكد من أن الخادم يعمل ---
@app.route('/')
def index():
    return "Bot server is alive and running!", 200

# --- تشغيل الخادم ---
if __name__ == '__main__':
    init_db()  # تهيئة قاعدة البيانات عند بدء التشغيل
    scheduler.start() # بدء جدولة المهام
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
