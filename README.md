# Book Management API with FastAPI

This is a simple **Book Management** project built with **FastAPI** and **PostgreSQL**.  
It allows you to add, search, and view books, along with uploading book images.

---

## Features

- Add a new book with title, author, publisher, and optional image.
- Search books by title, author, or publisher.
- View all books in a gallery-style grid.
- FastAPI backend with PostgreSQL database.
- Simple HTML/CSS frontend for interaction.

---

## Requirements

- Python 3.9+
- FastAPI
- Uvicorn
- Psycopg2
- Pydantic

Install the required packages:

```bash
pip install fastapi uvicorn psycopg2-binary pydantic
```

---

## Database Setup

This project uses **PostgreSQL**. You need to:

1. Install PostgreSQL if not already installed.
2. Create a new database:

```sql
CREATE DATABASE book_managementdb;
```

3. Create a table for books:

```sql
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher VARCHAR(100) NOT NULL,
    image_path VARCHAR(255)
);
```

4. Update the database connection settings in `main.py`:

```python
DB_HOST = "localhost"
DB_NAME = "book_managementdb"
DB_USER = "Your_PostgreSQL_Username"
DB_PASS = "Your_PostgreSQL_Password"
```

Replace `Your_PostgreSQL_Username` and `Your_PostgreSQL_Password` with your PostgreSQL credentials.

---

## Running the Project

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Open your browser and visit:

- Home page: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Add Book: `add_book.html`
- Search Books: `search_books.html`
- Say Hello: `say_hello.html`

---

## Project Structure

```
.
├── main.py           # FastAPI backend
├── images/           # Uploaded book images
├── add_book.html     # HTML form to add a new book
├── search_books.html # HTML page to search and view books
├── say_hello.html    # Simple "Hello" page
└── README.md         # This file
```

---

## Notes

- Book images are stored in the `images/` folder.
- If no image is uploaded, a default `book.png` is used.
- Search queries must be at least **3 characters** long.
- The frontend communicates with the backend via **HTTP requests** to the FastAPI endpoints.

---

## License

This project is open-source and free to use for learning and practice purposes.