from django.urls import path
from .views import ProductListCreate, ProductDetail, ProductReviewListCreate, ReviewDetail, CategoryListCreate, CategoryDetail, SearchEventTrack

urlpatterns = [
    path('products/', ProductListCreate.as_view()),
    path('products/<int:pk>/', ProductDetail.as_view()),
    path('products/<int:product_pk>/reviews/', ProductReviewListCreate.as_view()),
    path('products/<int:product_pk>/reviews/<int:review_id>/', ReviewDetail.as_view()),
    path('categories/', CategoryListCreate.as_view()),
    path('categories/<int:pk>/', CategoryDetail.as_view()),
    path('search/events/', SearchEventTrack.as_view()),
]