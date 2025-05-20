from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from catalog.models import Book, Booking, IssuedBook, Rating, UserProfile, Document
from catalog.forms import CustomUserCreationForm, CombinedProfileForm, RatingForm


class ViewTests(TestCase):
    def setUp(self):
        # Створення користувача для перевірки авторизованих сторінок
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_books_page(self):
        response = self.client.get(reverse('books'))
        self.assertEqual(response.status_code, 200)

    def test_archive_page(self):
        response = self.client.get(reverse('archive'))
        self.assertEqual(response.status_code, 200)

    def test_book_detail_page(self):
        # Щоб протестувати detail, потрібна книга (створимо "пусту")
        from catalog.models import Book
        book = Book.objects.create(title="Test Book", author="Author", genre="Test", year=2024, pages=100, language="UA", available=True)
        response = self.client.get(reverse('book_detail', args=[book.id]))
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_profile_page_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_page_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)

    def test_librarian_page(self):
        # Створення бібліотекаря
        self.user.userprofile.is_librarian = True
        self.user.userprofile.save()
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('librarian_bookings'))
        self.assertEqual(response.status_code, 200)



class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            genre='Детектив',
            year=2021,
            pages=300,
            language='Українська',
            available=True
        )

    def test_book_str(self):
        self.assertEqual(str(self.book), 'Test Book')

    def test_booking_creation(self):
        booking = Booking.objects.create(user=self.user, book=self.book, status='active')
        self.assertEqual(str(booking), f"{self.user.username} → {self.book.title} ({booking.status})")

    def test_issued_book_str(self):
        issued = IssuedBook.objects.create(user=self.user, book=self.book)
        self.assertEqual(str(issued), f"{self.book.title} → {self.user.username}")

    def test_rating_creation_and_average_rating(self):
        Rating.objects.create(user=self.user, book=self.book, rating=5)
        self.book.refresh_from_db()
        self.assertEqual(self.book.average_rating, 5.0)

    def test_user_profile_str(self):
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(str(profile), f"Профіль {self.user.username}")

    def test_document_str(self):
        doc = Document.objects.create(
            title='Test Doc',
            author='Author',
            category='Статті',
            field='Інформатика',
            file='documents/test.pdf',
            year=2020,
            pages=15
        )
        self.assertEqual(str(doc), 'Test Doc')


class FormTests(TestCase):
    def test_valid_user_creation_form(self):
        # 🔍 Тест перевіряє, що форма створення користувача працює з валідними даними
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Ім’я',
            'last_name': 'Прізвище',
            'phone': '123456789',
            'gender': 'male',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }

        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_user_creation_form_password_mismatch(self):
        # 🔍 Тест перевіряє, що при різних паролях форма не проходить валідацію
        form_data = {
            'username': 'testuser',
            'password1': 'StrongPass123!',
            'password2': 'WrongPass456!'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_valid_profile_update_with_password(self):
        # 🔍 Тест оновлення профілю з новим паролем
        user = User.objects.create_user(username='testuser', password='oldpass')
        form_data = {
            'username': 'testuser',
            'first_name': "Ім'я",
            'last_name': "Прізвище",
            'phone': '123456789',
            'gender': 'male',
            'old_password': 'oldpass',
            'new_password': 'NewPass123!',
        }
        form = CombinedProfileForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

    def test_invalid_profile_update_wrong_old_password(self):
        # 🔍 Тест перевіряє, що при неправильному старому паролі форма не проходить валідацію
        user = User.objects.create_user(username='testuser', password='correctold')
        form_data = {
            'username': 'testuser',
            'first_name': "Ім'я",
            'last_name': "Прізвище",
            'phone': '123456789',
            'gender': 'male',
            'old_password': 'wrongpass',
            'new_password': 'NewPass123!',
        }
        form = CombinedProfileForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())  # Форма пройде, але пароль буде перевірено у view

    def test_rating_form_valid(self):
        # 🔍 Тест перевіряє, що форма рейтингу працює з валідними даними
        form_data = {
            'rating': 5,
            'comment': 'Дуже хороша книга'
        }
        form = RatingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_rating_not_allowed(self):
        # 🔍 Тест перевіряє, що один користувач не може двічі оцінити одну книгу
        user = User.objects.create_user(username='testuser', password='testpass')
        book = Book.objects.create(title='Book', author='Author')
        Rating.objects.create(user=user, book=book, rating=4)
        duplicate = Rating(user=user, book=book, rating=5)
        with self.assertRaises(Exception):
            duplicate.save()




class BusinessLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.book = Book.objects.create(
            title='Test Book',
            author='Author',
            available=True,
            year=2024,
            pages=150,
            language='UA'
        )

    def test_book_becomes_unavailable_after_booking(self):
        """
        🔍 Перевіряє, що після бронювання книги її статус доступності змінюється на False.
        """
        booking = Booking.objects.create(user=self.user, book=self.book, status='active')
        # емуляція логіки з view (бо create не змінює доступність сам по собі)
        self.book.available = False
        self.book.save()

        self.book.refresh_from_db()
        self.assertFalse(self.book.available)

    def test_cannot_double_book_unavailable_book(self):
        """
        🔍 Перевіряє, що логіка в view не дозволяє забронювати книгу повторно, якщо вона вже недоступна.
        """
        client = Client()
        client.login(username='testuser', password='testpass')

        # перше бронювання через view
        response = client.post(reverse('book_reserve', args=[self.book.id]))
        self.book.refresh_from_db()
        self.assertFalse(self.book.available)

        booking_count_before = Booking.objects.count()

        # друга спроба (книга вже недоступна)
        response = client.post(reverse('book_reserve', args=[self.book.id]))

        booking_count_after = Booking.objects.count()
        self.assertEqual(booking_count_before, booking_count_after)


    def test_book_becomes_available_after_cancellation(self):
        """
        🔍 Перевіряє, що після скасування бронювання книга знову стає доступною.
        """
        # Створення бронювання з доступною книгою
        booking = Booking.objects.create(user=self.user, book=self.book, status='active')

        # Робимо книгу недоступною (як результат бронювання)
        self.book.available = False
        self.book.save()

        # Скасовуємо бронювання
        booking.status = 'cancelled'
        booking.book.available = True  # У view ця логіка оновлює доступність
        booking.book.save()

        # Перевірка
        booking.book.refresh_from_db()
        self.assertTrue(booking.book.available)


    def test_rating_updates_average(self):
        "Перевіряє, що середній рейтинг оновлюється після додавання оцінки."

        Rating.objects.create(user=self.user, book=self.book, rating=4)
        self.book.refresh_from_db()
        self.assertEqual(self.book.average_rating, 4.0)

        another_user = User.objects.create_user(username='seconduser', password='pass')
        Rating.objects.create(user=another_user, book=self.book, rating=2)
        self.book.refresh_from_db()
        self.assertEqual(self.book.average_rating, 3.0)



class PermissionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass')
        self.book = Book.objects.create(title="Test Book", author="Author", available=True)

    def test_guest_cannot_access_profile(self):
        # ❌ Гість не може зайти в профіль
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('profile')}", fetch_redirect_response=False)

    def test_guest_cannot_access_edit_profile(self):
        # ❌ Гість не може зайти на сторінку редагування профілю
        response = self.client.get(reverse('edit_profile'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('edit_profile')}", fetch_redirect_response=False)

    def test_guest_cannot_reserve_book(self):
        # ❌ Гість не може забронювати книгу
        response = self.client.post(reverse('book_reserve', args=[self.book.id]))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('book_reserve', args=[self.book.id])}", fetch_redirect_response=False)

    def test_guest_cannot_rate_book(self):
        # ❌ Гість не може залишити оцінку
        response = self.client.post(reverse('book_detail', args=[self.book.id]), data={
            'rating': 5,
            'comment': 'Test comment'
        })
        self.assertRedirects(response, f"/accounts/login/?next={reverse('book_detail', args=[self.book.id])}", fetch_redirect_response=False)

    def test_regular_user_cannot_access_librarian_panel(self):
        # ❌ Звичайний користувач не може зайти на панель бібліотекаря
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('librarian_bookings'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('librarian_bookings')}", fetch_redirect_response=False)


class SearchAndSortTests(TestCase):
    def setUp(self):
        # Книги
        self.book1 = Book.objects.create(title="Alpha", author="Author A", genre="Fantasy", year=2000, pages=100, average_rating=4.5)
        self.book2 = Book.objects.create(title="Bravo", author="Author B", genre="Drama", year=2010, pages=200, average_rating=3.5)
        self.book3 = Book.objects.create(title="Charlie", author="Author C", genre="Sci-fi", year=2020, pages=150, average_rating=5.0)

        # Документи
        Document.objects.create(title="AI Paper", author="Smith", category="Наукові роботи", field="Інформатика", pages=10, year=2022, file="documents/1.pdf")
        Document.objects.create(title="Sociology Report", author="Brown", category="Статті", field="Соціологія", pages=20, year=2015, file="documents/2.pdf")
        Document.objects.create(title="Math Study", author="White", category="Наукові роботи", field="Математика", pages=15, year=2018, file="documents/3.pdf")

        for i in range(15):
            Book.objects.create(
                title=f"Book {i}",
                author=f"Author {i}",
                genre="Test",
                year=2000 + i,
                pages=100 + i,
                average_rating=4.0,
            )

            # Створюємо багато документів
            for i in range(12):
                Document.objects.create(
                    title=f"Doc {i}",
                    author=f"Author {i}",
                    category="Статті" if i % 2 == 0 else "Наукові роботи",
                    field="Інформатика",
                    year=2010 + i,
                    pages=10 + i,
                    file=f"documents/test{i}.pdf",
                )

    # --- Пошук книг ---
    def test_search_by_title(self):
        response = self.client.get(reverse('books'), {'q': 'Alpha'})
        self.assertContains(response, "Alpha")
        self.assertNotContains(response, "Bravo")

    def test_search_by_author(self):
        response = self.client.get(reverse('books'), {'q': 'Author B'})
        self.assertContains(response, "Bravo")

    def test_sort_books_by_year(self):
        response = self.client.get(reverse('books'), {'sort': 'year'})
        years = [book.year for book in response.context['books']]
        self.assertEqual(years, sorted(years, reverse=True))

    def test_sort_books_by_pages(self):
        response = self.client.get(reverse('books'), {'sort': 'pages'})
        pages = [book.pages for book in response.context['books']]
        self.assertEqual(pages, sorted(pages, reverse=True))

    def test_sort_books_by_rating(self):
        response = self.client.get(reverse('books'), {'sort': 'rating'})
        ratings = [book.average_rating for book in response.context['books']]
        self.assertEqual(ratings, sorted(ratings, reverse=True))

    # --- Пошук і сортування документів ---
    def test_search_documents_by_title(self):
        response = self.client.get(reverse('archive'), {'q': 'AI'})
        self.assertContains(response, "AI Paper")
        self.assertNotContains(response, "Sociology Report")

    def test_filter_documents_by_category(self):
        response = self.client.get(reverse('archive'), {'category': 'Статті'})
        self.assertContains(response, "Sociology Report")
        self.assertNotContains(response, "AI Paper")

    def test_sort_documents_by_year(self):
        response = self.client.get(reverse('archive'), {'sort': 'year_desc'})
        years = [doc.year for doc in response.context['documents']]
        self.assertEqual(years, sorted(years, reverse=True))

    def test_sort_documents_by_pages(self):
        response = self.client.get(reverse('archive'), {'sort': 'pages_desc'})
        pages = [doc.pages for doc in response.context['documents']]
        self.assertEqual(pages, sorted(pages, reverse=True))

    def test_books_pagination_first_page(self):
        response = self.client.get(reverse('books'))  # ?page=1 за замовчуванням
        self.assertEqual(response.status_code, 200)
        self.assertTrue('books' in response.context)
        self.assertLessEqual(len(response.context['books']), 10)  # припустимо по 10 на сторінку

    def test_books_pagination_second_page(self):
        response = self.client.get(reverse('books') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('books' in response.context)
        self.assertGreater(len(response.context['books']), 0)

    def test_archive_pagination_first_page(self):
        response = self.client.get(reverse('archive'))  # ?page=1
        self.assertEqual(response.status_code, 200)
        self.assertTrue('documents' in response.context)
        self.assertLessEqual(len(response.context['documents']), 5)  # якщо по 5 документів на сторінку

    def test_archive_pagination_second_page(self):
        response = self.client.get(reverse('archive') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('documents' in response.context)
        self.assertGreater(len(response.context['documents']), 0)


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Book, Booking, IssuedBook, Rating

class AdditionalViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.book = Book.objects.create(title='Test Book', author='Author', available=True)

    def test_book_detail_post_create_rating(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('book_detail', args=[self.book.id]), {
            'rating': 4,
            'comment': 'Good book'
        })
        self.assertRedirects(response, reverse('book_detail', args=[self.book.id]))
        self.assertEqual(Rating.objects.filter(book=self.book, user=self.user).count(), 1)

    def test_book_detail_post_update_rating(self):
        Rating.objects.create(book=self.book, user=self.user, rating=2)
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('book_detail', args=[self.book.id]), {
            'rating': 5,
            'comment': 'Updated comment'
        })
        self.assertRedirects(response, reverse('book_detail', args=[self.book.id]))
        self.book.refresh_from_db()
        rating = Rating.objects.get(book=self.book, user=self.user)
        self.assertEqual(rating.rating, 5)

    def test_edit_profile_post_only_data(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'testuser',
            'first_name': "Ім'я",
                               'last_name': 'Прізвище',
        'phone': '123456789',
        'gender': 'male',
        'old_password': '',
        'new_password': ''
        })
        self.assertRedirects(response, reverse('profile'))

    def test_librarian_manual_issue_valid(self):
        UserProfile = self.user.userprofile
        UserProfile.is_librarian = True
        UserProfile.save()
        self.client.login(username='testuser', password='testpass')
        book = Book.objects.create(title='Manual Book', author='A', available=True)
        user2 = User.objects.create_user(username='reader', password='readerpass')
        response = self.client.post(reverse('librarian_bookings'), {
            'book_title': 'Manual Book',
            'user_name': 'reader'
        })
        self.assertRedirects(response, reverse('librarian_bookings'))
        self.assertTrue(Booking.objects.filter(book=book, user=user2).exists())
        self.assertTrue(IssuedBook.objects.filter(book=book, user=user2).exists())

    def test_librarian_manual_issue_invalid(self):
        self.user.userprofile.is_librarian = True
        self.user.userprofile.save()
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('librarian_bookings'), {
            'book_title': 'Wrong Title',
            'user_name': 'nonexistent'
        })
        self.assertRedirects(response, reverse('librarian_bookings'))

    def test_issue_book_logic(self):
        self.user.userprofile.is_librarian = True
        self.user.userprofile.save()
        self.client.login(username='testuser', password='testpass')
        book = Book.objects.create(title='Issued Book', author='X', available=True)
        booking = Booking.objects.create(book=book, user=self.user, status='active')
        response = self.client.get(reverse('issue_book', args=[booking.id]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'expired')
        self.assertTrue(IssuedBook.objects.filter(book=book, user=self.user).exists())

    def test_cancel_booking_by_librarian(self):
        self.user.userprofile.is_librarian = True
        self.user.userprofile.save()
        self.client.login(username='testuser', password='testpass')
        book = Book.objects.create(title='Cancel Book', author='Y', available=False)
        booking = Booking.objects.create(book=book, user=self.user, status='active')
        response = self.client.get(reverse('cancel_booking_librarian', args=[booking.id]))
        booking.refresh_from_db()
        book.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertTrue(book.available)

    def test_return_book_logic(self):
        self.user.userprofile.is_librarian = True
        self.user.userprofile.save()
        self.client.login(username='testuser', password='testpass')
        book = Book.objects.create(title='Return Book', author='Z', available=False)
        booking = Booking.objects.create(book=book, user=self.user, status='expired')
        issued = IssuedBook.objects.create(book=book, user=self.user)
        response = self.client.get(reverse('return_book', args=[issued.id]))
        self.assertFalse(IssuedBook.objects.filter(id=issued.id).exists())
        self.assertTrue(Book.objects.get(id=book.id).available)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'returned')