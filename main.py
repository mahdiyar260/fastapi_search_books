
from fastapi import FastAPI, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Optional, BinaryIO
from psycopg2 import pool
import psycopg2
import shutil
import json
import redis
import uuid
import os

#---------------DATA BASE---------------#

DB_HOST = "localhost"
DB_NAME = "book_managementdb"
DB_USER = "mahdiyar260"
DB_PASS = "m@2601007"

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    
    # Startup
    app.state.connection_pool = pool.SimpleConnectionPool(
        1,
        10,
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )
    
    yield  # App
    
    # Shutdown
    if app.state.connection_pool:
        app.state.connection_pool.closeall()

def get_connection() -> psycopg2.extensions.connection:
    return app.state.connection_pool.getconn()


#---------------REDIS/CACHE---------------#

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


#---------------APP & MODELS---------------#

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Book(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    author: str
    publisher: str
    image_path: str | None = None


#---------------END POINTS---------------#

@app.get("/")
def home():
    return {"message": "Welcome to Book Search API!"}


@app.post("/books/add", summary="Add a new book")
def add_book(
    title: str = Form(..., min_length=3, max_length=100),
    author: str = Form(...),
    publisher: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    
    max_file_size = 10 * 1024 * 1024  # 10 MB
    allowed_extensions = {"jpg", "jpeg", "png", "gif"}

    if image and image.filename != "":

        ext = image.filename.split(".")[-1].lower()
        if ext not in allowed_extensions:
            return {"error": f"File format not allowed. Allowed: {', '.join(allowed_extensions)}"}

        image.file.seek(0, os.SEEK_END)
        file_size = image.file.tell()
        image.file.seek(0)
        if file_size > max_file_size:
            return {"error": "File size exceeds 10 MB limit"}


        os.makedirs("images", exist_ok=True)
        filename = f"{uuid.uuid4().hex}_{image.filename}"
        image_path = f"images/{filename}"

        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
 
    else:
        image_path = "images/book.png"

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

        keys = r.get("search:*")
        if keys:
            r.delete(*keys)

    finally:
        app.state.connection_pool.putconn(conn)
    return {"message": "Book added successfully"}


@app.get("/books/search")
def search_books(
    query: str = Query(..., min_length=3, max_length=100),
    skip: int = 0,
    limit: int = 10
):

    cache_key = f"search:{query.lower()}:{skip}:{limit}"

    cached = r.get(cache_key)
    if cached:
        data = json.loads(cached)
        return {"from_cache": True, "results": data}

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM books
                WHERE LOWER(title) LIKE LOWER(%s)
                OR LOWER(author) LIKE LOWER(%s)
                OR LOWER(publisher) LIKE LOWER(%s)
                LIMIT %s OFFSET %s;
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%", limit, skip)
            )
            rows = cur.fetchall()

            r.set(cache_key, json.dumps(rows), ex=60)

            return rows
    finally:
        app.state.connection_pool.putconn(conn)


@app.get("/books/all")
def get_all_books(skip: int = 0, limit: int = 100):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM books LIMIT %s OFFSET %s;",
                (limit, skip)
            )
            return cur.fetchall()
    finally:
        app.state.connection_pool.putconn(conn)


@app.get("/books/count_by_author")
def count_books_by_author(author: str = Query(..., min_length=1, max_length=100)):
    """
    Return the number of books written by the given author.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM books WHERE author = %s;",
                (author,)
            )
            result = cur.fetchone()
            return {"author": author, "total_books": result[0]}
    finally:
        app.state.connection_pool.putconn(conn)


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello {name}!"}

#---------------ADD BOOKS---------------#
@app.post("/add_bulk/{count}")
def add_bulk_books(count: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for i in range(count):
                cur.execute(
                    """
                    INSERT INTO books (title, author, publisher, image_path)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        f"Book {i}",
                        f"Author {i % 100}",
                        "TestPublisher",
                        "images/book.png",
                    )
                )
        conn.commit()

        keys = r.keys("search:*")
        if keys:
            r.delete(*keys)

        return {"message": f"{count} books added successfully."}
    except Exception as e:
        return {"error": str(e)}
    finally:
        app.state.connection_pool.putconn(conn)



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
