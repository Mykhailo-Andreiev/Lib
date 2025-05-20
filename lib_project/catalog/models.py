# catalog/models.py
from django.db import models
from django.contrib.auth.models import User

# Модель книги
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    year = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=50, null=True, blank=True)
    available = models.BooleanField(default=True)
    average_rating = models.FloatField(default=0.0)
    image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=30, null=True, blank=True)
    is_recommended = models.BooleanField(default=False, verbose_name="Рекомендовано")

    def __str__(self):
        return self.title

# Бронювання книги
class Booking(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активно'),
        ('cancelled', 'Відмінено'),
        ('expired', 'Видано'),
        ('returned', 'Повернуто'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.user.username} → {self.book.title} ({self.status})"


# Видані книги
class IssuedBook(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.book.title} → {self.user.username}"

# Рейтинги книг
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(null=True, blank=True)
    rated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')  # Один користувач оцінює книгу тільки один раз

    def __str__(self):
        return f"{self.user.username} rated {self.book.title} as {self.rating}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        avg = Rating.objects.filter(book=self.book).aggregate(models.Avg('rating'))['rating__avg']
        self.book.average_rating = round(avg or 0, 2)
        self.book.save()

# Профіль користувача
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Чоловік'),
        ('female', 'Жінка'),
        ('other', 'Не вказано'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    is_librarian = models.BooleanField(default=False, verbose_name="Бібліотекар")

    def __str__(self):
        return f"Профіль {self.user.username}"

# Модель документів архіву
class Document(models.Model):
    CATEGORY_CHOICES = [
        ('Статті', 'Статті'),
        ('Наукові роботи', 'Наукові роботи'),
    ]

    FIELD_CHOICES = [
        ('Економіка', 'Економіка'),
        ('Соціологія', 'Соціологія'),
        ('Інформатика', 'Інформатика'),
        ('Математика', 'Математика'),
        ('Фізика', 'Фізика'),
    ]

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    field = models.CharField(max_length=50, choices=FIELD_CHOICES)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    year = models.PositiveIntegerField(null=True, blank=True, verbose_name='Рік публікації')
    pages = models.PositiveIntegerField(null=True, blank=True, verbose_name='Кількість сторінок')
    is_recommended = models.BooleanField(default=False)

    def __str__(self):
        return self.title
