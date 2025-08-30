from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterAPIView, LoginAPIView, BookViewSet, ReviewViewSet,
    BorrowBookAPIView, ReturnBookAPIView, MyBorrowedBooksAPIView,
    RecommendationAPIView
)

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("borrow/", BorrowBookAPIView.as_view(), name="borrow-book"),
    path("return/", ReturnBookAPIView.as_view(), name="return-book"),
    path("my-borrows/", MyBorrowedBooksAPIView.as_view(), name="my-borrows"),
    path("recommendations/", RecommendationAPIView.as_view(), name="recommendations"),
    path("", include(router.urls)),
]
