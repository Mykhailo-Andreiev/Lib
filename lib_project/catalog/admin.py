from django.contrib import admin
from .models import Book, Booking, IssuedBook, Rating, Document, UserProfile


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year', 'available', 'is_recommended')  # додай тут is_recommended
    list_filter = ('available', 'is_recommended')  # фільтр за рекомендованими
    search_fields = ('title', 'author')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'booking_date', 'status')
    list_filter = ('status', 'booking_date')
    search_fields = ('user__username', 'book__title')

@admin.register(IssuedBook)
class IssuedBookAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'issue_date', 'return_date')
    list_filter = ('issue_date', 'return_date')
    search_fields = ('user__username', 'book__title')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'rated_at')
    list_filter = ('rating',)
    search_fields = ('user__username', 'book__title')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'field', 'year', 'is_recommended')  # додай is_recommended
    list_filter = ('category', 'field', 'is_recommended')
    search_fields = ('title',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'gender', 'is_librarian')
    list_filter = ('is_librarian',)

