from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('books/', views.book_list, name='books'),  # 👈 це головний шлях
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/<int:book_id>/reserve/', views.book_reserve, name='book_reserve'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile_combined, name='edit_profile'),
    path('profile/password/', auth_views.PasswordChangeView.as_view(template_name='change_password.html'), name='password_change'),
    path('profile/password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='change_password_done.html'), name='password_change_done'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('archive/', views.archive, name='archive'),
    path('librarian/bookings/', views.librarian_bookings, name='librarian_bookings'),
    path('librarian/issue/<int:booking_id>/', views.issue_book, name='issue_book'),
    path('librarian/cancel/<int:booking_id>/', views.cancel_booking_by_librarian, name='cancel_booking_librarian'),
    path('librarian/return/<int:issued_id>/', views.return_book, name='return_book'),
    path('librarian/bookings/', views.librarian_bookings, name='librarian_bookings'),

]

