
from fastapi import FastAPI, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor 
from pydantic import BaseModel, Field
from typing import List, Optional
import psycopg2
import shutil
import os

# مشخصات اتصال به دیتابیس
DB_HOST = "localhost"
DB_NAME = "book_managementdb"
DB_USER = "Your_PostgreSQL_Username"
DB_PASS = "Your_PostgreSQL_Password"

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )


# -----------------------------
# مدل Pydantic
# -----------------------------
class Book(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    author: str
    publisher: str
    image_path: str | None = None

# -----------------------------
# اپلیکیشن FastAPI
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# لود کتاب‌ها از دیتابیس
# -----------------------------
def load_books() -> List[Book]:
    books = []
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM books;")
            rows = cur.fetchall()
            for r in rows:
                books.append(Book(**r))
    finally:
        conn.close()
    return books

# -----------------------------
# ذخیره کتاب‌ها روی دیتابیس
# -----------------------------
def save_books(books: List[Book]):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for b in books:
                if not b.image_path:
                    b.image_path = "images/book.png"
                cur.execute(
                    """
                    INSERT INTO books (title, author, publisher, image_path)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET title=EXCLUDED.title,
                        author=EXCLUDED.author,
                        publisher=EXCLUDED.publisher,
                        image_path=EXCLUDED.image_path;
                    """,
                    (b.title, b.author, b.publisher, b.image_path)
                )
        conn.commit()
    finally:
        conn.close()



# -----------------------------
# Home
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Book Search API!"}

# -----------------------------
# اضافه کردن کتاب جدید
# -----------------------------

@app.post("/books/add", summary="Add a new book")
def add_book(
    title: str = Form(..., min_length=3, max_length=100),
    author: str = Form(...),
    publisher: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    if not image or image.filename == "":
        image_path = "images/book.png"
    else:
        os.makedirs("images", exist_ok=True)  # اضافه کن قبل از open
        image_path = f"images/{image.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO books (title, author, publisher, image_path)
                VALUES (%s, %s, %s, %s);
                """,
                (title, author, publisher, image_path)
            )
        conn.commit()
    finally:
        conn.close()

    return {"message": "Book added successfully"}

# -----------------------------
# سرچ کتاب‌ها
# -----------------------------
@app.get("/books/search", summary="Search books by title, author, or publisher")
def search_books(
    query: str = Query(..., min_length=3, max_length=100, description="Text to search in title, author, or publisher"),
    skip: int = 0,
    limit: int = 10
):
    books = load_books()  # هر بار لود کتاب‌ها از فایل
    query_lower = query.lower()
    results = [book for book in books if query_lower in book.title.lower()
                                         or query_lower in book.author.lower()
                                         or query_lower in book.publisher.lower()]
    return results[skip: skip + limit]  # pagination

@app.get("/books/all", summary="Get all books")
def get_all_books(skip: int = 0, limit: int = 100):
    """
    Return all books in memory with optional pagination.
    """
    books = load_books()
    return [b.dict() for b in books][skip: skip + limit]

# -----------------------------
# سلام
# -----------------------------
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello {name}!"}





##############################################################################

#
#@app.get("/")
#def read_root():
#    return {"message": "Hello World!"}

#@app.get("/hello")
#def say_hello_query(name: str):
#    return {"message": f"Hello {name}!"}

#@app.get("/books", summary="Search books by title, author, or publisher")
#def search_books(query: str = Query(..., min_length=1, description="Text to search in title, author, or publisher")) -> List[Dict]:
#    """
#    Search for books that contain the query text in their title, author, or publisher.
#    """
#    results = []
#    query_lower = query.lower()
#    for book in books:
#        if query_lower in book["title"].lower() \
#           or query_lower in book["author"].lower() \
#           or query_lower in book["publisher"].lower():
#            results.append(book)
#    return results
