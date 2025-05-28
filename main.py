import telebot
import threading
import time
from datetime import datetime,timedelta,time as dtime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import jdatetime
from pytz import timezone
import sqlite3
from db_utills import connect_db, create_tables, save_reminders_to_db, load_reminders_from_db,delete_reminder_from_db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton



def get_db_connection():
    return sqlite3.connect('reminders.db')

tehran = timezone('Asia/Tehran')



TOKEN = "7846223492:AAHdm7Ur7vGh6aNNdT69lb0WS8Qx5f_SR5o"  # توکن بات خود را اینجا قرار دهید
bot = telebot.TeleBot(TOKEN)

# ساختار داده‌ای برای ذخیره یادآورها
reminders = {}  # {chat_id: [{'time': datetime, 'message': str, 'created_at': datetime}, ...]}
user_names = {}
date_reminder = {}
daily_reminders = {}


# اتصال به دیتابیس
conn, cursor = connect_db()
# ساخت جدول‌ها
create_tables(cursor)
#لود
load_reminders_from_db(cursor, reminders, daily_reminders)


def check_reminders():
    while True:
        current_time = datetime.now(tehran)
        for chat_id, items in list(reminders.items()):
            for reminder in items[:]:
                if reminder['time'] <= current_time:
                    name = user_names.get(chat_id, "دوست من")
                    bot.send_message(chat_id, f"سلام {name}!\n📌 {reminder['message']}")
                    items.remove(reminder)
        time.sleep(5)

# شروع یک ترد جدید برای بررسی یادآورها
reminder_thread = threading.Thread(target=check_reminders, daemon=True)
reminder_thread.start()

def check_daily_reminders():
    while True:
        now = datetime.now(tehran).time()
        for chat_id, items in daily_reminders.items():
            for item in items:
                if item['time'].hour == now.hour and item['time'].minute == now.minute and 0 <= datetime.now(tehran).second < 5:
                    name = user_names.get(chat_id, "دوست گشاد من")
                    bot.send_message(chat_id, f"🔁 پیام روزانه برای {name}:\n{item['message']}")
        time.sleep(5)
# اجرای ترد دوم
daily_thread = threading.Thread(target=check_daily_reminders, daemon=True)
daily_thread.start()

@bot.message_handler(commands=['daily'])
def set_daily_reminder(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, " لطفاً زمان و پیام یادآور روزانه را به این شکل بفرست:\n\nمثال: `08:30 پاشو سرباززز`")
    bot.register_next_step_handler(message, process_daily_reminder)



def process_daily_reminder(message):
    chat_id = message.chat.id
    try:
        time_str, msg = message.text.strip().split(' ', 1)
        hour, minute = map(int, time_str.split(':'))
        reminder_time = dtime(hour, minute)

        if chat_id not in daily_reminders:
            daily_reminders[chat_id] = []

        daily_reminders[chat_id].append({
            'time': reminder_time,
            'message': msg
        })
        save_reminders_to_db(conn, cursor, reminders, daily_reminders)

        # پیام موفقیت
        print(f"Sending success message for daily reminder to {chat_id}")
        bot.send_message(chat_id, f"✅ پیام روزانه تنظیم شد: {hour:02d}:{minute:02d} - {msg}")

    except Exception as e:
        print(f"Error in process_daily_reminder: {e}")
        bot.send_message(chat_id, "قالب اشتباهه! مثلا بگو: 08:15 بیدار شو")



@bot.message_handler(commands=['dateremind'])
def set_date_reminder(message):
    chat_id = message.chat.id
    bot.send_message(message.chat.id, "تاریخ شمسی، ساعت و پیام رو وارد کن به شکل زیر:\n\n1404-03-05 17:22 پیام مورد نظر")
    bot.register_next_step_handler(message, process_determined_reminder)

def process_determined_reminder(message):
    chat_id = message.chat.id
    text = message.text.strip()

    try:
        parts = text.split(' ', 2)
        if len(parts) < 3:
            raise ValueError("فرمت نادرست")

        date_str, time_str, msg = parts
        date_parts = list(map(int, date_str.split('-')))
        time_parts = list(map(int, time_str.split(':')))

        if len(date_parts) != 3 or len(time_parts) != 2:
            raise ValueError("تاریخ یا ساعت اشتباهه")

        jdate = jdatetime.date(*date_parts)
        gdate = jdatetime.datetime(jdate.year, jdate.month, jdate.day,
                                   time_parts[0], time_parts[1]).togregorian()
        timestamp = gdate.strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("reminders.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (chat_id, reminder_type, time, message, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, 'determined', timestamp, msg, 1))
        conn.commit()
        conn.close()

        bot.send_message(chat_id, f"✅ یادآور تنظیم شد برای {date_str} ساعت {time_str}: {msg}")
        print(f"✅ Determined reminder set for {chat_id} at {timestamp}")

    except Exception as e:
        print(f"❌ خطا در تنظیم یادآور تاریخ‌دار: {e}")
        bot.send_message(chat_id, "❗️قالب پیام اشتباه است. لطفاً به این شکل بنویس:\n`1403-03-10 14:30 برو کلاس زبان`")




@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "سلام! خوش اومدی 😊\n\n اسمت چیه ماهی گلی من؟")
    bot.register_next_step_handler(message, save_user_name)
def save_user_name(message):
    chat_id = message.chat.id
    name =user_names.get(chat_id,"")
    user_names[chat_id] = message.text.strip()
    """راهنمای استفاده از بات"""
    help_text = f"""
⏰ *به بات الزایمر خوش اومدی {name}*

اینجا مخصوص افرادی ست که که از الزایمر رنج میبرند
ببین خودتم میدونی حافظت عین ماهی گلیه
پس بیا و زور نزن عزیزم
این ربات مخصوص خودته(سوسیس نیست)
استفاده از این ربات برای عموم ازاد است
جیزز کرایست با شما باشد

*دستورات:*
/remind - تنظیم یادآور جدید
/daily - یه پیام خاص رو تو یه ساعت خاص برات میفرستم
/dateremind - اون یاد اوره رو واسه یه روز خاص میفرستم فقط
/list - نمایش لیست یادآورهای فعال
/help - نمایش این راهنما


اگه میخوای یه پیام همین امروز یه ساعتی همینجوری بهت یاد اوری بشه:
*نحوه استفاده:*
1. دستور /remind را ارسال کنید
2. زمان و متن یادآوری را در قالب `ساعت:دقیقه و بعدش متن یادآوری که میخوای` وارد کنید
3. در زمان مشخص شده، پیام یادآوری دریافت خواهید کرد

اگه میخوای یه روز دیگه یه چیزی بهت یاد اوری بشه:
1: دستور /dateremind رو بزن
2:پیام رو به شکل زیر وارد کن:
YYYY-MM-DD HH:MM متن پیام
مثال: 2025-06-01 10:30 آزمون ریاضی
تاریخ ایرانیم بزنی اوکیه

اگه میخوای روزانه یه پیامی که خودت دوس داری برات بفرستم :
1:بزن /daily
2:زمان و متن پیام روزانه رو به این شکل وارد کن:
ساعت:دقیقه متن پیام
مثال: 08:15 وقت لالاعه!

یه سری دستور چرت:
/stop ربات از کار میفته و از بدبختی میمیری
/resume اگه stop زده بودی و به غلط کردن افتادی این گزینه رو بزن عسیسم میدونم طاقت دوری نداشتی
/list لیست ندونم کار هاتو بهت میگم عسل بابا

                    مرگ بر خانه سالمندان
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['remind', 'reminder'])
def handle_reminder(message):
    """دستور ایجاد یادآور جدید"""
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "لطفاً یادآور خود را در این قالب وارد کنید:\n"
        "ساعت:دقیقه متن یادآوری\n\n"
        "مثال: 14:30 جلسه با مدیر"
    )
    bot.register_next_step_handler(message, process_reminder)

def process_reminder(message):
    """پردازش متن یادآوری وارد شده توسط کاربر"""
    chat_id = message.chat.id
    text = message.text.strip()
    
    try:
        # جداسازی زمان و متن یادآوری
        time_str, reminder_text = text.split(' ', 1)
        hour, minute = map(int, time_str.split(':'))
        
        # ایجاد زمان یادآوری
        now = datetime.now()
        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # اگر زمان تنظیم شده قبل از زمان فعلی باشد، آن را برای فردا تنظیم می‌کنیم
        if reminder_time < now:
            from datetime import timedelta
            reminder_time += timedelta(days=1)
        
        # ایجاد یادآور جدید
        if chat_id not in reminders:
            reminders[chat_id] = []
        
        reminders[chat_id].append({
            'time': reminder_time,
            'message': reminder_text,
            'created_at': now
        })
        save_reminders_to_db(conn, cursor, reminders, daily_reminders)

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO reminders (chat_id, time, message, created_at) VALUES (?, ?, ?, ?)',
                  (chat_id, reminder_time.isoformat(), reminder_text, now.isoformat()))
        conn.commit()
        conn.close()
        

        # نمایش تأیید به کاربر
        bot.send_message(
            chat_id,
            f"✅ یادآور برای ساعت {hour:02d}:{minute:02d} تنظیم شد:\n{reminder_text}"
        )
        
    except Exception as e:
        bot.send_message(
            chat_id,
            "❌ فرمت وارد شده صحیح نیست. لطفاً دوباره تلاش کنید.\n"
            "مثال: 14:30 جلسه با مدیر"
        )

@bot.message_handler(commands=['myreminders', 'list'])
def list_reminders(message):
    """نمایش لیست یادآورهای کاربر"""
    chat_id = message.chat.id
    user_reminders = reminders.get(chat_id, [])
    
    if not user_reminders:
        bot.send_message(chat_id, "شما هیچ یادآوری فعالی ندارید.")
        return
    
    # مرتب‌سازی یادآورها بر اساس زمان
    user_reminders.sort(key=lambda x: x['time'])
    
    response = "📋 *یادآورهای شما:*\n\n"
    for i, reminder in enumerate(user_reminders, 1):
        time_str = reminder['time'].strftime("%H:%M")
        response += f"{i}. ساعت {time_str}: {reminder['message']}\n"
    
    # ایجاد دکمه‌های حذف یادآورها
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    
    for i in range(len(user_reminders)):
        markup.add(InlineKeyboardButton(
            f"حذف #{i+1}", 
            callback_data=f"delete_reminder_{i}"
        ))
    
    bot.send_message(chat_id, response, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_reminder_'))
def delete_reminder(call):
    chat_id = call.message.chat.id
    parts = call.data.split('_')  # مثلاً ['delete', 'reminder', 'daily', '5']
    
    if len(parts) != 4:
        bot.answer_callback_query(call.id, "خطای داخلی")
        return
    
    reminder_type = parts[2]  # 'daily' یا 'dated'
    reminder_id = int(parts[3])  # آیدی یادآور

    # حذف از دیتابیس
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=? AND type=? AND chat_id=?", (reminder_id, reminder_type, chat_id))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "یادآور با موفقیت حذف شد.")
    bot.edit_message_text("✅ یادآور حذف شد.", chat_id=chat_id, message_id=call.message.message_id)


@bot.message_handler(commands=['list'])
def list_reminders(message):
    chat_id = message.chat.id
    conn = sqlite3.connect("reminders.db")
    c = conn.cursor()

    types = ['dated', 'daily']
    for reminder_type in types:
        c.execute("SELECT id, time, message FROM reminders WHERE chat_id=? AND type=?", (chat_id, reminder_type))
        reminders = c.fetchall()

        if reminders:
            kind = 'تاریخ‌دار' if reminder_type == 'dated' else 'روزانه'
            text = f"📋 لیست یادآورهای {kind}:\n\n"
            markup = InlineKeyboardMarkup()

            for r_id, r_time, r_msg in reminders:
                text += f"🕒 {r_time} - {r_msg}\n"
                delete_btn = InlineKeyboardButton(
                    f"❌ حذف {r_time}",
                    callback_data=f"delete_reminder_{reminder_type}_{r_id}"
                )
                markup.add(delete_btn)

            bot.send_message(chat_id, text, reply_markup=markup)
        else:
            kind = 'تاریخ‌دار' if reminder_type == 'dated' else 'روزانه'
            bot.send_message(chat_id, f"⛔️ یادآور {kind}ی نداری.")

    conn.close()


# شروع به کار بات
print("bot is working")
bot.polling(none_stop=True)
