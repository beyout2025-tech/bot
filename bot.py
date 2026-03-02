import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

BOT_TOKEN = "7936382345:AAEpQBnIfJzZX9YstGi2aTochaPIss6T9BI"
ADMIN_ID = 873158772
DATA_FILE = "courses.json"

# ===================== تحميل وحفظ البيانات =====================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": [], "courses": []}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

data = load_data()

# ===================== أزرار =====================
def back_to_main_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 رجوع", callback_data="main_menu")]])

def main_menu_kb(user_id: int):
    rows = [[InlineKeyboardButton("📚 استعراض الدورات", callback_data="show_courses")]]
    if user_id == ADMIN_ID:
        rows.append([InlineKeyboardButton("➕ إضافة دورة", callback_data="add_course")])
    return InlineKeyboardMarkup(rows)

def courses_kb(user_id: int):
    keyboard, row = [], []
    for idx, course in enumerate(data["courses"]):
        row.append(InlineKeyboardButton(course["name"], callback_data=f"course_{idx}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    tail = [InlineKeyboardButton("🏠 رجوع", callback_data="main_menu")]
    if user_id == ADMIN_ID:
        tail.append(InlineKeyboardButton("➕ إضافة دورة", callback_data="add_course"))
    keyboard.append(tail)
    return InlineKeyboardMarkup(keyboard)

def course_details_kb(idx: int, is_admin: bool):
    row = [
        InlineKeyboardButton("⬅️ رجوع", callback_data="show_courses"),
        InlineKeyboardButton("📥 التسجيل في الدورة", callback_data=f"register_{idx}")
    ]
    if is_admin:
        row += [
            InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_{idx}"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"del_{idx}")
        ]
    return InlineKeyboardMarkup([row])

# ===================== /start =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)
        await context.bot.send_message(
            ADMIN_ID,
            f"👤 مستخدم جديد دخل البوت:\nID: {user_id}\nName: {update.effective_user.first_name}"
        )
    await update.message.reply_text(
        "🌟 مرحبًا بك في بوت مؤسسة 'كن أنت للتدريب والتأهيل' 🎓",
        reply_markup=main_menu_kb(user_id)
    )

# ===================== عرض الدورات =====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "main_menu":
        await q.edit_message_text("🏠 القائمة الرئيسية:", reply_markup=main_menu_kb(q.from_user.id))
        return

    if q.data == "show_courses":
        if not data["courses"]:
            await q.edit_message_text("❌ لا توجد دورات حالياً.", reply_markup=main_menu_kb(q.from_user.id))
            return
        await q.edit_message_text("📚 اختر دورة لعرض التفاصيل:", reply_markup=courses_kb(q.from_user.id))
        return

    if q.data.startswith("course_"):
        idx = int(q.data.split("_")[1])
        course = data["courses"][idx]
        text = f"📖 {course['name']}\n\n{course['description']}\n💰 رسوم الدورة: {course['price']}"
        await q.edit_message_text(text, reply_markup=course_details_kb(idx, q.from_user.id == ADMIN_ID))
        return

    # معالجة أمر التعديل
    if q.data.startswith("edit_"):
        await edit_start(update, context)
        return

    # معالجة أمر الحذف
    if q.data.startswith("del_"):
        await delete_start(update, context)
        return

# ===================== إضافة دورة =====================
ADD_NAME, ADD_DESC, ADD_PRICE = range(3)

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.from_user.id != ADMIN_ID:
        await q.message.reply_text("❌ صلاحية المدير فقط.", reply_markup=back_to_main_kb())
        return ConversationHandler.END
    await q.message.reply_text("📝 أرسل اسم الدورة:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_course"] = {"name": update.message.text}
    await update.message.reply_text("📝 أرسل وصف الدورة:")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_course"]["description"] = update.message.text
    await update.message.reply_text("💰 أرسل رسوم الدورة:")
    return ADD_PRICE

async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_course"]["price"] = update.message.text
    data["courses"].append(context.user_data["new_course"])
    save_data(data)
    await update.message.reply_text("✅ تم إضافة الدورة بنجاح!", reply_markup=back_to_main_kb())
    return ConversationHandler.END

# ===================== التسجيل خطوة بخطوة =====================
REGISTER_NAME, REGISTER_GENDER, REGISTER_AGE, REGISTER_COUNTRY, REGISTER_CITY, REGISTER_PHONE, REGISTER_EMAIL = range(7)

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    idx = int(q.data.split("_")[1])
    context.user_data["register_course_idx"] = idx
    context.user_data["register_data"] = {"course_name": data["courses"][idx]["name"]}
    await q.message.reply_text("📝 أرسل الاسم الثلاثي:", reply_markup=back_to_main_kb())
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["register_data"]["name"] = update.message.text
    await update.message.reply_text("📝 أرسل الجنس:", reply_markup=back_to_main_kb())
    return REGISTER_GENDER

async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["register_data"]["gender"] = update.message.text
    await update.message.reply_text("📝 أرسل العمر:", reply_markup=back_to_main_kb())
    return REGISTER_AGE

async def register_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["register_data"]["age"] = update.message.text
    await update.message.reply_text("📝 أرسل البلد:", reply_markup=back_to_main_kb())
    return REGISTER_COUNTRY

async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["register_data"]["country"] = update.message.text
    await update.message.reply_text("📝 أرسل المدينة:", reply_markup=back_to_main_kb())
    return REGISTER_CITY

async def register_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["register_data"]["city"] = update.message.text
    await update.message.reply_text("📝 أرسل رقم الهاتف (يجب أن يكون واتساب):", reply_markup=back_to_main_kb())
    return REGISTER_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["register_data"]["phone"] = update.message.text
    await update.message.reply_text("📝 أرسل البريد الإلكتروني:", reply_markup=back_to_main_kb())
    return REGISTER_EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data_user = context.user_data["register_data"]
    data_user["email"] = update.message.text
    data_user["telegram_username"] = user.username if user.username else "❌ لا يوجد"
    data_user["telegram_id"] = user.id

    # رسالة للمستخدم مع زر رجوع
    await update.message.reply_text(
        "✅ تم إرسال جميع البيانات إلى الإدارة، سيتم التواصل معك في أقرب وقت ممكن.",
        reply_markup=back_to_main_kb()
    )

    # رسالة للمطور مع أزرار القبول/الرفض
    idx_course = context.user_data["register_course_idx"]
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user.id}_{idx_course}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user.id}_{idx_course}")
        ]
    ]
    text = (
        f"📥 طلب انضمام جديد\n"
        f"📖 الدورة: {data_user['course_name']}\n"
        f"1- الاسم الثلاثي: {data_user['name']}\n"
        f"2- الجنس: {data_user['gender']}\n"
        f"3- العمر: {data_user['age']}\n"
        f"4- البلد: {data_user['country']}\n"
        f"5- المدينة: {data_user['city']}\n"
        f"6- رقم الهاتف: {data_user['phone']}\n"
        f"7- البريد الإلكتروني: {data_user['email']}\n"
        f"8- معرف التيلجرام: @{data_user['telegram_username']}\n"
        f"🆔 ID: {data_user['telegram_id']}"
    )
    await context.bot.send_message(ADMIN_ID, text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


# ===================== قبول/رفض من المطور =====================
ACCEPT_MESSAGE, REJECT_MESSAGE = range(2)

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    action, user_id, course_idx = parts[0], int(parts[1]), int(parts[2])

    # حفظ البيانات في context.user_data للمتابعة في المحادثة
    context.user_data['temp_user_id'] = user_id
    context.user_data['temp_course_idx'] = course_idx
    context.user_data['message_to_edit'] = query.message.message_id
    context.user_data['chat_id_to_edit'] = query.message.chat_id

    # رسالة إلى المدير مع زر للإلغاء
    cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="cancel_action")]])

    if action == "accept":
        await query.message.reply_text("✅ تم اختيار القبول. الآن، أرسل رسالة القبول للمستخدم:", reply_markup=cancel_kb)
        return ACCEPT_MESSAGE
    elif action == "reject":
        await query.message.reply_text("❌ تم اختيار الرفض. الآن، أرسل رسالة الرفض للمستخدم:", reply_markup=cancel_kb)
        return REJECT_MESSAGE

async def send_accept_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('temp_user_id')
    course_idx = context.user_data.get('temp_course_idx')
    message_to_edit = context.user_data.get('message_to_edit')
    chat_id_to_edit = context.user_data.get('chat_id_to_edit')

    user_message = update.message.text
    course_name = data["courses"][course_idx]["name"] if course_idx < len(data["courses"]) else "❌ الدورة غير موجود"

    try:
        # إرسال الرسالة المخصصة للمستخدم
        await context.bot.send_message(user_id, user_message)

        # تعديل رسالة المدير الأصلية
        await context.bot.edit_message_text(
            chat_id=chat_id_to_edit,
            message_id=message_to_edit,
            text=f"✅ تم القبول في دورة: {course_name}\n\n**الرسالة المرسلة:**\n{user_message}",
            reply_markup=None
        )
        await update.message.reply_text("✅ تم إرسال رسالة القبول بنجاح.", reply_markup=back_to_main_kb())

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء إرسال الرسالة للمستخدم: {e}", reply_markup=back_to_main_kb())

    return ConversationHandler.END

async def send_reject_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('temp_user_id')
    course_idx = context.user_data.get('temp_course_idx')
    message_to_edit = context.user_data.get('message_to_edit')
    chat_id_to_edit = context.user_data.get('chat_id_to_edit')

    user_message = update.message.text
    course_name = data["courses"][course_idx]["name"] if course_idx < len(data["courses"]) else "❌ الدورة غير موجود"

    try:
        # إرسال الرسالة المخصصة للمستخدم
        await context.bot.send_message(user_id, user_message)

        # تعديل رسالة المدير الأصلية
        await context.bot.edit_message_text(
            chat_id=chat_id_to_edit,
            message_id=message_to_edit,
            text=f"❌ تم الرفض في دورة: {course_name}\n\n**الرسالة المرسلة:**\n{user_message}",
            reply_markup=None
        )
        await update.message.reply_text("✅ تم إرسال رسالة الرفض بنجاح.", reply_markup=back_to_main_kb())

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء إرسال الرسالة للمستخدم: {e}", reply_markup=back_to_main_kb())

    return ConversationHandler.END

async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("تم إلغاء العملية.")
    await query.message.reply_text("✅ تم إلغاء العملية.", reply_markup=back_to_main_kb())
    return ConversationHandler.END


# ===================== تعديل وحذف دورة =====================
EDIT_NAME, EDIT_DESC, EDIT_PRICE = range(3)

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("❌ صلاحية المدير فقط.", reply_markup=back_to_main_kb())
        return ConversationHandler.END

    idx = int(query.data.split("_")[1])
    context.user_data['edit_idx'] = idx

    keyboard = [
        [InlineKeyboardButton("تعديل الاسم", callback_data="edit_name")],
        [InlineKeyboardButton("تعديل الوصف", callback_data="edit_desc")],
        [InlineKeyboardButton("تعديل الرسوم", callback_data="edit_price")]
    ]
    await query.message.reply_text("✏️ اختر ما تريد تعديله:", reply_markup=InlineKeyboardMarkup(keyboard))
    return 'edit_choice' # العودة إلى الحالة الرئيسية لـ edit_conv

async def edit_select_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    field = query.data.split("_")[1]
    context.user_data['edit_field'] = field

    await query.message.reply_text(f"📝 أرسل القيمة الجديدة لـ {field}:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء", callback_data="cancel_action")]]))

    if field == "name":
        return 'edit_name'
    elif field == "desc":
        return 'edit_desc'
    elif field == "price":
        return 'edit_price'

async def save_edited_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get('edit_idx')
    field = context.user_data.get('edit_field')
    new_value = update.message.text

    if field == "name":
        data["courses"][idx]["name"] = new_value
    elif field == "desc":
        data["courses"][idx]["description"] = new_value
    elif field == "price":
        data["courses"][idx]["price"] = new_value

    save_data(data)
    await update.message.reply_text(f"✅ تم تعديل {field} بنجاح.", reply_markup=back_to_main_kb())
    return ConversationHandler.END

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text("❌ صلاحية المدير فقط.", reply_markup=back_to_main_kb())
        return ConversationHandler.END

    idx = int(query.data.split("_")[1])
    context.user_data['delete_idx'] = idx

    keyboard = [[InlineKeyboardButton("✅ تأكيد الحذف", callback_data="confirm_delete"),
                 InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")]]

    course_name = data["courses"][idx]["name"]
    await query.message.reply_text(f"⚠️ هل أنت متأكد من حذف دورة '{course_name}'؟", reply_markup=InlineKeyboardMarkup(keyboard))
    return 'delete_confirm' # العودة إلى حالة التأكيد

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = context.user_data.get('delete_idx')
    course_name = data["courses"][idx]["name"]
    del data["courses"][idx]
    save_data(data)

    await query.edit_message_text(f"🗑️ تم حذف دورة '{course_name}' بنجاح.", reply_markup=back_to_main_kb())
    return ConversationHandler.END


# ===================== تشغيل البوت =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # محادثة إضافة دورة
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_start, pattern="add_course")],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
        },
        fallbacks=[]
    )
    app.add_handler(add_conv)

    # محادثة تسجيل دورة خطوة بخطوة
    register_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(register_start, pattern="register_")],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_gender)],
            REGISTER_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_age)],
            REGISTER_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_country)],
            REGISTER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_city)],
            REGISTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
        },
        fallbacks=[]
    )
    app.add_handler(register_conv)

    # محادثة تعديل دورة
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_start, pattern="edit_")],
        states={
            'edit_choice': [CallbackQueryHandler(edit_select_field, pattern="^(edit_name|edit_desc|edit_price)$")],
            'edit_name': [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_field)],
            'edit_desc': [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_field)],
            'edit_price': [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_field)],
        },
        fallbacks=[CallbackQueryHandler(cancel_action, pattern="cancel_action")]
    )
    app.add_handler(edit_conv)

    # محادثة حذف دورة
    delete_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_start, pattern="del_")],
        states={
            'delete_confirm': [CallbackQueryHandler(confirm_delete, pattern="confirm_delete")]
        },
        fallbacks=[CallbackQueryHandler(cancel_action, pattern="cancel_action")]
    )
    app.add_handler(delete_conv)

    # محادثة القبول والرفض المخصصة
    admin_decision_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_decision, pattern="^(accept|reject)_")],
        states={
            ACCEPT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_accept_message)],
            REJECT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_reject_message)],
        },
        fallbacks=[CallbackQueryHandler(cancel_action, pattern="cancel_action")]
    )
    app.add_handler(admin_decision_conv)

    # الأزرار العامة الأخرى
    app.add_handler(CallbackQueryHandler(button_handler))


    print("✅ البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
