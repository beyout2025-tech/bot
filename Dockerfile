# اختر نسخة Python مستقرة (3.11)
FROM python:3.11-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع إلى الحاوية
COPY requirements.txt .
COPY bot.py .
COPY courses.json .  # إذا كنت تستخدم ملف بيانات

# تثبيت المكتبات
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# تعيين متغير البيئة للبوت
ENV BOT_TOKEN=your_bot_token_here

# تشغيل البوت مباشرة عند تشغيل الحاوية
CMD ["python", "bot.py"]
