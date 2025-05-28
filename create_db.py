import sqlite3

conn = sqlite3.connect('reminders.db')
c = conn.cursor()

# جدول یادآورهای همون روز
c.execute('''
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    message TEXT NOT NULL,
    reminder_type TEXT NOT NULL
)

''')


# جدول یادآورهای تاریخ‌دار
c.execute('''
CREATE TABLE IF NOT EXISTS date_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    datetime TEXT NOT NULL,
    message TEXT NOT NULL
)
''')

# جدول یادآورهای روزانه
c.execute('''
CREATE TABLE IF NOT EXISTS daily_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    message TEXT NOT NULL
)
''')

conn.commit()
conn.close()
