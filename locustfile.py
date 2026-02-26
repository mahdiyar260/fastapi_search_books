import random
from locust import HttpUser, task, between

class BookUser(HttpUser):
    wait_time = between(1, 3)

    # ---------------- SEARCH ----------------
    @task(5)
    def search_books(self):
        queries = ["Book", "Author", "Test", "Publisher", "1"]
        q = random.choice(queries)
        self.client.get(f"/books/search?query={q}")

    # ---------------- GET ALL ----------------
    @task(2)
    def get_all_books(self):
        skip = random.randint(0, 50)
        self.client.get(f"/books/all?skip={skip}&limit=20")

    # ---------------- COUNT BY AUTHOR ----------------
    @task(1)
    def count_by_author(self):
        author_id = random.randint(0, 50)
        self.client.get(f"/books/count_by_author?author=Author {author_id}")

    # ---------------- HELLO ----------------
    @task(1)
    def say_hello(self):
        name = random.choice(["Ali", "Sara", "Reza", "Mahdi"])
        self.client.get(f"/hello/{name}")

    # ---------------- ADD BOOK ----------------
    @task(1)
    def add_book(self):
        self.client.post(
            "/books/add",
            data={
                "title": f"LoadTestBook {random.randint(1,10000)}",
                "author": "Locust",
                "publisher": "PerformanceTest"
            }
        )