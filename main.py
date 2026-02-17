
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List, Dict

with open("books.json", "r", encoding = "utf-8") as f:
    books = json.load(f)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to Book Search API!"}

@app.get("/books", summary="Search books by title, author, or publisher")
def search_books(query: str = Query(..., min_length=1, description="Text to search in title, author, or publisher")) -> List[Dict]:
    """
    Search for books that contain the query text in their title, author, or publisher.
    """
    results = []
    query_lower = query.lower()
    for book in books:
        if query_lower in book["title"].lower() \
           or query_lower in book["author"].lower() \
           or query_lower in book["publisher"].lower():
            results.append(book)
    return results

#
#@app.get("/")
#def read_root():
#    return {"message": "Hello World!"}

@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello {name}!"}

#@app.get("/hello")
#def say_hello_query(name: str):
#    return {"message": f"Hello {name}!"}
