from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Book, BorrowRecord, Review
from .serializers import (
    BookSerializer, BorrowRecordSerializer, ReviewSerializer,
    RegisterSerializer
)


# ---------------- PAGINATION -----------------
class BookPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# ---------------- USER REGISTRATION -----------------
class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": {"id": user.id, "username": user.username},
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


# ---------------- USER LOGIN -----------------
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"detail": "Username and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"},
                            status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": {"id": user.id, "username": user.username},
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)


# ---------------- BOOK VIEWSET -----------------
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by("-created_at")
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = BookPagination

    def get_queryset(self):
        qs = super().get_queryset()
        genre = self.request.query_params.get("genre")
        author = self.request.query_params.get("author")
        available = self.request.query_params.get("available")

        if genre:
            qs = qs.filter(genre__iexact=genre)
        if author:
            qs = qs.filter(author__icontains=author)
        if available is not None:
            if available.lower() in ("1", "true", "yes"):
                qs = qs.filter(available_copies__gt=0)
            else:
                qs = qs.filter(available_copies__lte=0)
        return qs


# ---------------- REVIEW VIEWSET -----------------
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().select_related("user", "book")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------------- BORROW BOOK -----------------
class BorrowBookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        book_id = request.data.get("book_id")
        if not book_id:
            return Response({"detail": "book_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.select_for_update().get(pk=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        # Prevent double borrowing
        if BorrowRecord.objects.filter(user=request.user, book=book, returned_at__isnull=True).exists():
            return Response({"detail": "You already borrowed this book and haven't returned it."},
                            status=status.HTTP_400_BAD_REQUEST)

        if book.available_copies <= 0:
            return Response({"detail": "No copies available"}, status=status.HTTP_400_BAD_REQUEST)

        # Update book copies
        book.available_copies = F('available_copies') - 1
        book.save()
        book.refresh_from_db()

        borrow_record = BorrowRecord.objects.create(user=request.user, book=book)
        serializer = BorrowRecordSerializer(borrow_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---------------- RETURN BOOK -----------------
class ReturnBookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        book_id = request.data.get("book_id")
        if not book_id:
            return Response({"detail": "book_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.select_for_update().get(pk=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            borrow_record = BorrowRecord.objects.select_for_update().get(
                user=request.user, book=book, returned_at__isnull=True
            )
        except BorrowRecord.DoesNotExist:
            return Response({"detail": "You do not have this book borrowed right now."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Mark returned
        borrow_record.returned_at = timezone.now()
        borrow_record.save()

        # Update book stats
        book.available_copies = F('available_copies') + 1
        book.read_count = F('read_count') + 1
        book.save()
        book.refresh_from_db()

        serializer = BorrowRecordSerializer(borrow_record)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------- MY BORROWED BOOKS -----------------
class MyBorrowedBooksAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_borrows = BorrowRecord.objects.filter(
            user=request.user, returned_at__isnull=True
        ).select_related("book")
        serializer = BorrowRecordSerializer(active_borrows, many=True)
        return Response(serializer.data)


# ---------------- RECOMMENDATIONS -----------------
class RecommendationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        limit = int(request.query_params.get("limit", 5))

        # 1️⃣ Recommend based on user borrowing history (same genre)
        if user:
            borrowed_genres = Book.objects.filter(
                borrow_records__user=user
            ).values_list("genre", flat=True).distinct()

            if borrowed_genres:
                recommended_books = Book.objects.filter(
                    genre__in=borrowed_genres
                ).exclude(
                    borrow_records__user=user, borrow_records__returned_at__isnull=True
                ).order_by('-read_count', '-created_at')[:limit]

                if recommended_books:
                    serializer = BookSerializer(recommended_books, many=True)
                    return Response(serializer.data)

        # 2️⃣ Fallback to top globally popular books
        popular_books = Book.objects.all().order_by('-read_count', '-created_at')[:limit]
        serializer = BookSerializer(popular_books, many=True)
        return Response(serializer.data)

