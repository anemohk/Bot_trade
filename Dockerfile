FROM python:3.10-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# إنشاء مجلد العمل
WORKDIR /app

# نسخ الملفات المطلوبة
COPY requirements.txt .
COPY bot.py .

# تثبيت الاعتمادات
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# الأمر التشغيلي
CMD ["gunicorn", "bot:app", "-b", "0.0.0.0:5000", "--timeout", "120"]
