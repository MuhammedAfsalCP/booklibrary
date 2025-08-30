from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Book, BorrowRecord

class BookLendingAPITest(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client = APIClient()

        # Create books
        self.book1 = Book.objects.create(title="Book One", author="Author A", genre="Fiction", available_copies=3, read_count=5)
        self.book2 = Book.objects.create(title="Book Two", author="Author B", genre="History", available_copies=2, read_count=10)
        self.book3 = Book.objects.create(title="Book Three", author="Author A", genre="Fiction", available_copies=0, read_count=8)

        # URLs
        self.login_url = reverse("login")
        self.books_url = reverse("book-list")
        self.borrow_url = reverse("borrow-book")
        self.return_url = reverse("return-book")
        self.my_borrows_url = reverse("my-borrows")
        self.recommendations_url = reverse("recommendations")

    # ---------------- USER AUTH -----------------
    def test_user_login(self):
        response = self.client.post(self.login_url, {"username": "testuser", "password": "password123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    # ---------------- BOOK LIST -----------------
    def test_list_books(self):
        response = self.client.get(self.books_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Support pagination
        books = response.data.get("results", response.data)
        titles = [book["title"] for book in books]
        self.assertCountEqual(titles, [self.book1.title, self.book2.title, self.book3.title])

    def test_book_filters(self):
        # Filter by genre
        response = self.client.get(self.books_url, {"genre": "Fiction"})
        books = response.data.get("results", response.data)
        for book in books:
            self.assertEqual(book["genre"], "Fiction")

        # Filter by author
        response = self.client.get(self.books_url, {"author": "Author B"})
        books = response.data.get("results", response.data)
        for book in books:
            self.assertIn("Author B", book["author"])

        # Filter by availability
        response = self.client.get(self.books_url, {"available": "true"})
        books = response.data.get("results", response.data)
        for book in books:
            self.assertGreater(book["available_copies"], 0)

    # ---------------- BORROW BOOK -----------------
    def test_borrow_book_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.borrow_url, {"book_id": self.book1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BorrowRecord.objects.filter(user=self.user, book=self.book1, returned_at__isnull=True).count(), 1)

    def test_borrow_same_book_twice(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.borrow_url, {"book_id": self.book1.id})
        response = self.client.post(self.borrow_url, {"book_id": self.book1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_borrow_unavailable_book(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.borrow_url, {"book_id": self.book3.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---------------- RETURN BOOK -----------------
    def test_return_book_success(self):
        self.client.force_authenticate(user=self.user)
        borrow = BorrowRecord.objects.create(user=self.user, book=self.book2)
        response = self.client.post(self.return_url, {"book_id": self.book2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrow.refresh_from_db()
        self.assertIsNotNone(borrow.returned_at)

    # ---------------- MY BORROWED BOOKS -----------------
    def test_my_borrowed_books(self):
        self.client.force_authenticate(user=self.user)
        BorrowRecord.objects.create(user=self.user, book=self.book1)
        response = self.client.get(self.my_borrows_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["book"]["title"], self.book1.title)

    # ---------------- RECOMMENDATIONS -----------------
    def test_recommendations_with_history(self):
        self.client.force_authenticate(user=self.user)
        # Borrow a book in Fiction genre
        BorrowRecord.objects.create(user=self.user, book=self.book1)
        response = self.client.get(self.recommendations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        books = response.data
        # All recommended books should not include the borrowed one
        borrowed_ids = BorrowRecord.objects.filter(user=self.user, returned_at__isnull=True).values_list("book_id", flat=True)
        for book in books:
            self.assertNotIn(book["id"], borrowed_ids)

    def test_recommendations_fallback(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.recommendations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        books = response.data
        self.assertGreaterEqual(len(books), 1)
        read_counts = [book["read_count"] for book in books]
        self.assertEqual(read_counts, sorted(read_counts, reverse=True))
