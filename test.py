
import psycopg2

# اطلاعات اتصال
DB_HOST = "localhost"
DB_NAME = "book_managementdb"
DB_USER = "Mahdiyar260"
DB_PASS = "m@2601007"

# اتصال به دیتابیس
conn = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS
)

# ساخت یک کرسر برای اجرای دستورات SQL
cur = conn.cursor()

# ایجاد جدول books
cur.execute("""
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher VARCHAR(100) NOT NULL,
    image_path TEXT
)
""")

conn.commit()
