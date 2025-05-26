import telebot
import threading
import time
from datetime import datetime,timedelta,time as dtime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import jdatetime
TOKEN = "7846223492:AAHdm7Ur7vGh6aNNdT69lb0WS8Qx5f_SR5o"  # توکن بات خود را اینجا قرار دهید
bot = telebot.TeleBot(TOKEN)

# ساختار داده‌ای برای ذخیره یادآورها
reminders = {}  # {chat_id: [{'time': datetime, 'message': str, 'created_at': datetime}, ...]}
user_names = {}
date_reminder = {}


def check_reminders():
    """بررسی مداوم یادآورها برای ارسال در زمان مناسب"""
    while True:
        current_time = datetime.now()
        for chat_id in list(reminders.keys()):
            user_reminders = reminders.get(chat_id, [])
            for reminder in user_reminders[:]:
                reminder_time = reminder.get('time')
                if isinstance(reminder_time, datetime) and reminder_time <= current_time:
                    try:
                        name = user_names.get(chat_id, "دوست گشاد من")
                        bot.send_message(
                            chat_id,
                            f"سلام {name}\n"
                            f"!اینم یادآور امروزت گشاد بازی در نیار:\n\n"
                            f"📌 {reminder['message']}",
                            parse_mode='Markdown'
                        )
                        reminders[chat_id].remove(reminder)
                    except Exception as e:
                        print(f"Error sending reminder: {e}")
        time.sleep(10)

# شروع یک ترد جدید برای بررسی یادآورها
reminder_thread = threading.Thread(target=check_reminders, daemon=True)
reminder_thread.start()

def check_daily_reminders():
    """ارسال پیام روزانه در ساعت مشخص"""
    while True:
        now = datetime.now()
        for chat_id, data in reminders.items():
            reminder_time = data['time']
            # اگر زمان برابر شد (دقیقه به دقیقه)
            if now.hour == reminder_time.hour and now.minute == reminder_time.minute and now.second < 10:
                try:
                    name = user_names.get(chat_id,"دوست گشاد من")
                    bot.send_message(chat_id, f"*یه پیام دارم واسه {name}*\n\n{data['message']}", parse_mode='Markdown')
                except Exception as e:
                    print(f"Error in daily reminder: {e}")
        time.sleep(10)

# اجرای ترد دوم
daily_thread = threading.Thread(target=check_daily_reminders, daemon=True)
daily_thread.start()

@bot.message_handler(commands=['daily'])
def set_daily_reminder(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "لطفاً زمان و پیام روزانه را وارد کنید:\n\nقالب:\nساعت:دقیقه پیام موردنظر")
    bot.register_next_step_handler(message, process_daily_reminder)

def process_daily_reminder(message):
    chat_id = message.chat.id
    try:
        time_str, text = message.text.strip().split(' ', 1)
        hour, minute = map(int, time_str.split(':'))
        reminders[chat_id] = {
            'time': dtime(hour, minute),
            'message': text
        }
        bot.send_message(chat_id, f"✅ پیام روزانه شما در ساعت {hour:02d}:{minute:02d} تنظیم شد.")
    except:
        bot.send_message(chat_id, """داری اشتب میزنی باید اینجوری بنویسی:
                         مثلا:07:05 پاشو سرباز وقت جنگه""")


@bot.message_handler(commands=['dateremind'])
def set_date_reminder(message):
    chat_id = message.chat.id
    bot.send_message(message.chat.id, "تاریخ شمسی، ساعت و پیام رو وارد کن به شکل زیر:\n\n1404-03-05 17:22 پیام مورد نظر")
    bot.register_next_step_handler(message, process_determind)

def process_determind(message):
    chat_id = message.chat.id
    text = message.text.strip()

    try:
        date_part, time_part, msg = text.split(' ', 2)
        year, month, day = map(int, date_part.split('-'))
        hour, minute = map(int, time_part.split(':'))

        # تبدیل تاریخ شمسی به میلادی
        jalali_date = jdatetime.date(year, month, day)
        gregorian_date = jalali_date.togregorian()

        reminder_time = datetime(
            gregorian_date.year, gregorian_date.month, gregorian_date.day,
            hour, minute
        )

        if chat_id not in reminders:
            reminders[chat_id] = []

        reminders[chat_id].append({
            'time': reminder_time,
            'message': msg,
            'created_at': datetime.now()
        })

        bot.send_message(chat_id, f" یادآور برای {date_part} ساعت {hour:02d}:{minute:02d} ثبت شد:\n{msg}")

    except Exception as e:
        bot.send_message(chat_id, " فرمتت اشتباهه مشتی. باید این‌طوری باشه:\n1404-03-15 16:00 زاییدنم ")




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
    """حذف یادآور انتخاب شده"""
    chat_id = call.message.chat.id
    user_reminders = reminders.get(chat_id, [])
    
    # استخراج شاخص یادآور
    try:
        reminder_index = int(call.data.split('_')[-1])
        if 0 <= reminder_index < len(user_reminders):
            # حذف یادآور
            deleted_reminder = user_reminders.pop(reminder_index)
            time_str = deleted_reminder['time'].strftime("%H:%M")
            
            bot.answer_callback_query(call.id, "یادآور با موفقیت حذف شد.")
            bot.edit_message_text(
                f"✅ یادآور ساعت {time_str} حذف شد.",
                chat_id=chat_id,
                message_id=call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "یادآور یافت نشد.")
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "خطا در حذف یادآور.")

# شروع به کار بات
print("bot is working")
bot.polling(none_stop=True)
