# استخدم نسخة Python مستقرة مناسبة مع python-telegram-bot
FROM python:3.11-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع إلى الحاوية
COPY . /app

# تحديث pip وتثبيت المتطلبات
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# إعداد متغير البيئة لتمكين تشغيل البوت
ENV BOT_TOKEN=${BOT_TOKEN}

# أمر تشغيل البوت
CMD ["python", "bot.py"]
