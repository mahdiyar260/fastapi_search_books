
from fastapi import FastAPI, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Optional
import redis.asyncio as aioredis
from dotenv import load_dotenv
import asyncpg
import shutil
import json
import uuid
import os

#---------------DATA BASE---------------#

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
REDIS_URL = os.getenv("REDIS_URL")

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):

    fastapi_app.state.pg_pool = await asyncpg.create_pool( # type: ignore
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        min_size=1,
        max_size=10,
    )

    yield

    await fastapi_app.state.pg_pool.close()


#---------------REDIS/CACHE---------------#

r = aioredis.from_url(REDIS_URL, decode_responses=True)


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
async def home():
    return {"message": "Welcome to Book Search API!"}


@app.post("/books/add", summary="Add a new book")
async def add_book(
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
            shutil.copyfileobj(image.file, buffer) # type: ignore
 
    else:
        image_path = "images/book.png"

    async with app.state.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO books (title, author, publisher, image_path)
            VALUES ($1, $2, $3, $4)
            """,
            title, author, publisher, image_path
        )

    # پاک کردن کش
    keys = r.keys("search:*")
    if keys:
        await r.delete(*keys)

    return {"message": "Book added successfully"}


@app.get("/books/search")
async def search_books(
    query: str = Query(..., min_length=3, max_length=100),
    skip: int = 0,
    limit: int = 10
):

    cache_key = f"search:{query.lower()}:{skip}:{limit}"

    cached = await r.get(cache_key)
    if cached:
        data = json.loads(cached)
        return {"from_cache": True, "results": data}

    async with app.state.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM books
            WHERE LOWER(title) LIKE LOWER($1)
            OR LOWER(author) LIKE LOWER($1)
            OR LOWER(publisher) LIKE LOWER($1)
            LIMIT $2 OFFSET $3;
            """,
            f"%{query}%",
            limit,
            skip
        )
        result = [dict(row) for row in rows]

    await r.set(cache_key, json.dumps(result), ex=60)

    return rows


@app.get("/books/all")
async def get_all_books(skip: int = 0, limit: int = 100):
    cache_key = f"all_books:{skip}:{limit}"
    cached = await r.get(cache_key)
    if cached:
        data = json.loads(cached)
        return {"from_cache": True, "results": data}

    async with app.state.pg_pool.acquire() as conn:

        rows = await conn.fetch(
            "SELECT * FROM books LIMIT $1 OFFSET $2;",
            limit,
            skip
        )

        result = [dict(row) for row in rows]

    await r.set(cache_key, json.dumps(result), ex=60)
    return result


@app.get("/books/count_by_author")
async def count_books_by_author(author: str = Query(..., min_length=1, max_length=100)):

    cache_key = f"count_by_author:{author}"
    cached = await r.get(cache_key)
    if cached:
        data = json.loads(cached)
        return {"from_cache": True, "results": data}

    async with app.state.pg_pool.acquire() as conn:
        result = await conn.fetch(
            "SELECT COUNT(*) AS total FROM books WHERE author = $1;",
            author
        )
    total_books = result[0]["total"] if result else 0
    await r.set(cache_key, json.dumps(total_books), ex=60)
    return {"author": author, "total_books": total_books}



@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}!"}

#---------------ADD BOOKS---------------#
@app.post("/add_bulk/{count}")
async def add_bulk_books(count: int):

    async with app.state.pg_pool.acquire() as conn:
        for i in range(count):
            await conn.execute(
                """
                INSERT INTO books (title, author, publisher, image_path)
                VALUES ($1, $2, $3, $4)
                """,
                (
                    f"Book {i}",
                    f"Author {i % 100}",
                    "TestPublisher",
                    "images/book.png",
                )
            )

    keys = r.keys("search:*")
    if keys:
        await r.delete(*keys)

    return {"message": f"{count} books added successfully."}


##############################################################################
"""
async def get_connection():
    async with app.state.pg_pool.acquire() as conn:
        yield conn
"""
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
