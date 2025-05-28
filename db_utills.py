import sqlite3
from datetime import datetime

def connect_db():
    conn = sqlite3.connect('reminders.db', check_same_thread=False)
    cursor = conn.cursor()
    return conn, cursor

def create_tables(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            time TEXT,
            message TEXT,
            reminder_type TEXT
        )
    ''')

def save_reminders_to_db(conn, cursor, reminders, daily_reminders):
    cursor.execute('DELETE FROM reminders')

    for chat_id, items in reminders.items():
        for item in items:
            cursor.execute('''
                INSERT INTO reminders (chat_id, time, message, reminder_type)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, item['time'].isoformat(), item['message'], 'remind'))

    for chat_id, items in daily_reminders.items():
        for item in items:
            time_str = datetime.combine(datetime.today(), item['time']).isoformat()
            cursor.execute('''
                INSERT INTO reminders (chat_id, time, message, reminder_type)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, time_str, item['message'], 'daily'))

    conn.commit()

def load_reminders_from_db(cursor, reminders, daily_reminders):
    cursor.execute('SELECT chat_id, time, message, reminder_type FROM reminders')
    rows = cursor.fetchall()

    for chat_id, time_str, message, reminder_type in rows:
        chat_id = int(chat_id)
        time_obj = datetime.fromisoformat(time_str)

        if reminder_type == 'daily':
            if chat_id not in daily_reminders:
                daily_reminders[chat_id] = []
            daily_reminders[chat_id].append({
                'time': time_obj.time(),
                'message': message
            })
        else:
            if chat_id not in reminders:
                reminders[chat_id] = []
            reminders[chat_id].append({
                'time': time_obj,
                'message': message,
                'created_at': datetime.now()
            })

def delete_reminder_from_db(cursor, chat_id, reminder_time, message):
    cursor.execute(
        "DELETE FROM reminders WHERE chat_id = ? AND time = ? AND message = ?",
        (chat_id, reminder_time.isoformat(), message)
    )
