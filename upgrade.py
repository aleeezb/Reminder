import sqlite3

conn = sqlite3.connect("reminders.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE reminders ADD COLUMN is_active INTEGER DEFAULT 1")
    print("ستون is_active اضافه شد.")
except sqlite3.OperationalError as e:
    print("❗️احتمالاً ستون از قبل وجود داره یا مشکلی در اجرای دستور هست:")
    print(e)

conn.commit()
conn.close()
