from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Avg

from .forms import CustomUserCreationForm, CombinedProfileForm, RatingForm
from .models import Book, Booking, Rating, Document, IssuedBook


# Реєстрація
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# Головна сторінка
def home(request):
    recommended_books = Book.objects.filter(is_recommended=True)[:5]
    recommended_articles = Document.objects.filter(category="Статті", is_recommended=True).order_by('-year')[:5]
    recommended_works = Document.objects.filter(category="Наукові роботи", is_recommended=True).order_by('-year')[:5]

    return render(request, 'home.html', {
        'recommended_books': recommended_books,
        'recommended_articles': recommended_articles,
        'recommended_works': recommended_works,
    })


# Каталог книг
def book_list(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "")
    books = Book.objects.all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(genre__icontains=query)
        )

    if sort == "year":
        books = books.order_by("-year")
    elif sort == "pages":
        books = books.order_by("-pages")
    elif sort == "rating":
        books = books.order_by("-average_rating")

    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    books_page = paginator.get_page(page_number)

    return render(request, "books.html", {
        "books": books_page,
        "query": query
    })


# Деталі книги + оцінки
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    ratings = Rating.objects.filter(book=book)
    average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    if request.method == 'POST' and not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next={request.path}")

    user_rating = None
    form = RatingForm()

    if request.user.is_authenticated:
        user_rating = ratings.filter(user=request.user).first()
        if request.method == 'POST':
            form = RatingForm(request.POST, instance=user_rating)
            if form.is_valid():
                rating = form.save(commit=False)
                rating.user = request.user
                rating.book = book
                rating.save()
                return redirect('book_detail', book_id=book.id)
        else:
            form = RatingForm(instance=user_rating)

    return render(request, 'book_detail.html', {
        'book': book,
        'ratings': ratings,
        'form': form,
        'user_rating': user_rating,
        'book_average': round(average_rating, 1),
    })


# Бронювання
@login_required
def book_reserve(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if book.available:
        Booking.objects.create(
            user=request.user,
            book=book,
            status='active'
        )
        book.available = False
        book.save()

    return redirect('book_detail', book_id=book.id)

# Профіль користувача
@login_required
def profile(request):
    bookings = Booking.objects.filter(user=request.user).select_related('book').order_by('-booking_date')
    return render(request, 'profile.html', {'bookings': bookings})


# Редагування профілю + зміна пароля
@login_required
def edit_profile_combined(request):
    user = request.user
    if request.method == 'POST':
        form = CombinedProfileForm(request.POST, instance=user)
        if form.is_valid():
            old = form.cleaned_data.get('old_password')
            new = form.cleaned_data.get('new_password')

            if new:
                if not user.check_password(old):
                    form.add_error('old_password', 'Неправильний старий пароль.')
                    return render(request, 'edit_profile.html', {'form': form})
                user.set_password(new)
                update_session_auth_hash(request, user)

            form.save()
            return redirect('profile')
    else:
        form = CombinedProfileForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form})


# Відміна бронювання
@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status == 'active':
        booking.status = 'cancelled'
        booking.book.available = True
        booking.book.save()
        booking.save()
    return redirect('profile')


# Архів
def archive(request):
    category = request.GET.get('category')
    field = request.GET.get('field')
    query = request.GET.get('q')
    sort = request.GET.get('sort')

    documents = Document.objects.all()

    if query:
        documents = documents.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if category:
        documents = documents.filter(category__iexact=category)
    if field:
        documents = documents.filter(field__iexact=field)
    if sort == 'year_asc':
        documents = documents.order_by('year')
    elif sort == 'year_desc':
        documents = documents.order_by('-year')
    elif sort == 'pages_asc':
        documents = documents.order_by('pages')
    elif sort == 'pages_desc':
        documents = documents.order_by('-pages')

    paginator = Paginator(documents, 5)
    page = request.GET.get('page')
    documents = paginator.get_page(page)

    return render(request, 'archive.html', {
        'documents': documents,
    })


# Перевірка ролі бібліотекаря
def is_librarian(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.is_librarian


# Панель бібліотекаря
@user_passes_test(is_librarian)
def librarian_bookings(request):
    query = request.GET.get('q', '')
    issued_query = request.GET.get('iq', '')

    if request.method == 'POST':
        book_title = request.POST.get('book_title', '').strip()
        user_name = request.POST.get('user_name', '').strip()

        try:
            book = Book.objects.get(title__iexact=book_title)
            user = User.objects.get(username__iexact=user_name)
        except (Book.DoesNotExist, User.DoesNotExist):
            return redirect('librarian_bookings')

        IssuedBook.objects.create(book=book, user=user, issue_date=timezone.now())
        Booking.objects.create(book=book, user=user, booking_date=timezone.now(), status='expired')
        book.available = False
        book.save()

        return redirect('librarian_bookings')

    booking_list = Booking.objects.select_related('book', 'user').order_by('-booking_date')
    if query:
        booking_list = booking_list.filter(Q(book__title__icontains=query) | Q(user__username__icontains=query))

    bookings = Paginator(booking_list, 5).get_page(request.GET.get('page'))

    issued_list = IssuedBook.objects.select_related('book', 'user').order_by('-issue_date')
    if issued_query:
        issued_list = issued_list.filter(Q(book__title__icontains=issued_query) | Q(user__username__icontains=issued_query))

    issued_books = Paginator(issued_list, 5).get_page(request.GET.get('ipage'))

    books = Book.objects.all()
    users = User.objects.all()

    return render(request, 'librarian/bookings.html', {
        'bookings': bookings,
        'issued_books': issued_books,
        'books': books,
        'users': users,
    })


# Видати книгу
@user_passes_test(is_librarian)
def issue_book(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.status == 'active':
        booking.status = 'expired'
        booking.book.available = False
        booking.book.save()
        booking.save()
        IssuedBook.objects.create(book=booking.book, user=booking.user)
    return redirect('librarian_bookings')


# Скасувати бронювання (бібліотекар)
@user_passes_test(is_librarian)
def cancel_booking_by_librarian(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.status == 'active':
        booking.status = 'cancelled'
        booking.book.available = True
        booking.book.save()
        booking.save()
    return redirect('librarian_bookings')


# Повернення книги
@user_passes_test(is_librarian)
def return_book(request, issued_id):
    issued = get_object_or_404(IssuedBook, id=issued_id)
    booking = Booking.objects.filter(book=issued.book, user=issued.user).order_by('-booking_date').first()
    if booking:
        booking.status = 'returned'
        booking.save()
    issued.book.available = True
    issued.book.save()
    issued.delete()
    return redirect('librarian_bookings')
